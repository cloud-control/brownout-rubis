#include "controller.h"

#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>

#include <Python.h>

static double now()
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return ts.tv_nsec / 1000000000.0 + ts.tv_sec;
}

#define LOG(level, fmt, ...) fprintf(stderr, "[%lf][%s][%s] " fmt "\n%c", now(), __func__, level, __VA_ARGS__)

#define LOG_INFO(...)  LOG("info", __VA_ARGS__, 0)
#define LOG_WARN(...)  LOG("warn", __VA_ARGS__, 0)
#define LOG_ERROR(...) LOG("error", __VA_ARGS__, 0)

struct controller_s {
    PyObject *pController;
    PyObject *pRunControlLoop;
    int current_queue_length;
};

typedef struct {
    PyObject_HEAD
    controller_t c;
} Sim;

staticforward PyTypeObject SimType;


#define ABORT_WITH_PYERR(...) \
    do { \
        if (PyErr_Occurred()) \
            PyErr_Print(); \
        LOG_ERROR(__VA_ARGS__); \
        exit(1); \
    } while(0)

controller_t controller_init() {
    controller_t c = malloc(sizeof(struct controller_s));
    char *fake_argv[] = { "" };

    Py_SetProgramName(fake_argv[0]);
    Py_Initialize();
    PySys_SetArgv(0, fake_argv);

    PyObject* sysPath = PySys_GetObject((char*)"path");
    PyObject* curDir = PyString_FromString("./brownout-lb-simulator");
    PyList_Insert(sysPath, 0, curDir);
    Py_DECREF(curDir);

    PyObject *pName = PyString_FromString("controllers.server.cf_cascaded");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule == 0)
        ABORT_WITH_PYERR("Could not load Python module; aborting");

    PyRun_SimpleString(
        "import argparse\n"
        "import controllers.server.cf_cascaded as controllerModule\n"
        "parser = argparse.ArgumentParser()\n"
        "controllerModule.addCommandLine(parser)\n"
        "args = parser.parse_args(['--CCOuterPeriod', '0.5'])\n"
        "controllerModule.parseCommandLine(args)\n"
    );

    PyObject *pNewInstance = PyObject_GetAttrString(pModule, "newInstance");
    if (pNewInstance == 0)
        ABORT_WITH_PYERR("Could not find newInstance in Python controller; aborting");
    Py_DECREF(pModule);

    if (PyCallable_Check(pNewInstance) == 0)
        ABORT_WITH_PYERR("newInstance in Python controller is not callable; aborting");

    PyType_Ready(&SimType);
    Sim *pSim = PyObject_New(Sim, &SimType);
    pSim->c = c;

    PyObject *pArgs = PyTuple_New(2);
    PyTuple_SetItem(pArgs, 0, (PyObject *)pSim);
    PyTuple_SetItem(pArgs, 1, PyString_FromString("pyController0"));
    c->pController = PyObject_CallObject(pNewInstance, pArgs);
    Py_DECREF(pArgs);
    Py_DECREF(pNewInstance);

    if (c->pController == 0)
        ABORT_WITH_PYERR("Could not create new instance of controller; aborting");

    c->current_queue_length = 0;

    return c;
}

void controller_free(controller_t c) {
    Py_Finalize();

    free(c);
}

int controller_with_optional(controller_t c, int queue_length) {
    int ret = 0;
    PyObject *pRet;

    pRet = PyObject_CallMethod(c->pController, "reportData", "ididdi", true, 0.0, 0, 0.0, 0.0, false);
    if (pRet == 0)
        PyErr_Print();
    Py_XDECREF(pRet);

    pRet = PyObject_CallMethod(c->pController, "withOptional", "i", queue_length-1);
    PyObject *pFirst = PyTuple_GetItem(pRet, 0);
    if (pFirst == Py_True)
        ret = 1;
    else if (pFirst == Py_False)
        ret = 0;
    else
        LOG_ERROR("withOptional returned invalid value");
    Py_DECREF(pRet);

    c->current_queue_length++;

    return ret;
}

void controller_report(controller_t c, double response_time, int queue_length, int with_optional) {
    c->current_queue_length--;

    PyObject *pRet = PyObject_CallMethod(c->pController, "reportData", "ididdi",
            false, response_time, queue_length-1, 0.0, 0.0, with_optional);
    if (pRet == 0)
        PyErr_Print();
    Py_XDECREF(pRet);
}

char *controller_upstream_info(controller_t c) {
    PyObject *pRet = PyObject_GetAttrString(c->pController, "queueLengthSetpoint");
    if (!pRet) {
        LOG_ERROR("queueLengthSetpoint not found");
        return 0;
    }

    PyObject *pRetStr = PyObject_Str(pRet);
    Py_DECREF(pRet);

    if (!pRetStr) {
        LOG_ERROR("queueLengthSetpoint not convertible to string");
        return 0;
    }

    char *ret;
    ret = strdup(PyString_AsString(pRetStr));
    Py_DECREF(pRetStr);

    return ret;
}

void controller_run_control_loop(controller_t c) {
    if (c->pRunControlLoop) {
        PyObject *toCall = c->pRunControlLoop;
        c->pRunControlLoop = 0;

        PyObject *pRet = PyObject_Call(toCall, PyTuple_New(0), NULL);
        if (pRet == 0)
            PyErr_Print();
        Py_XDECREF(pRet);

        Py_DECREF(toCall);
    }
}

static PyObject *
Sim_add(Sim* self, PyObject *args) {
    if (PyTuple_Size(args) != 2) {
        LOG_ERROR("takes exactly 2 arguments (%ld given)", PyTuple_Size(args));
        PyErr_BadArgument();
        return 0;
    }

    PyObject *pWhen = PyTuple_GetItem(args, 0);
    PyObject *pCallback = PyTuple_GetItem(args, 1);

    double when = PyFloat_AsDouble(pWhen);
    if (PyErr_Occurred()) {
        LOG_ERROR("argument 1 must be float");
        PyErr_BadArgument();
        return 0;
    }

    if (PyCallable_Check(pCallback) == 0) {
        LOG_ERROR("argument 2 must be callable");
        PyErr_BadArgument();
        return 0;
    }

    if (when != 0.5)
        LOG_WARN("This (fake) simulator only supports events 1 second into the future (%lf requested)", when);

    Py_INCREF(pCallback);
    self->c->pRunControlLoop = pCallback;

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
Sim_output(Sim* self, PyObject *args) {
    if (PyTuple_Size(args) != 2) {
        LOG_ERROR("takes exactly 2 arguments (%ld given)", PyTuple_Size(args));
        PyErr_BadArgument();
        return 0;
    }

    char *who = NULL;
    PyObject *pWho = PyTuple_GetItem(args, 0);
    if (pWho) {
        pWho = PyObject_Str(pWho);
        who = PyString_AsString(pWho);
    }

    LOG_INFO("[%s] %s",
            who,
            PyString_AsString(PyTuple_GetItem(args, 1)));

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
Sim_getattr(PyObject *sim, PyObject *attr_name) {
    if (strcmp(PyString_AsString(attr_name), "now") == 0)
        return PyFloat_FromDouble(now());
    return PyObject_GenericGetAttr(sim, attr_name);
}

static PyMethodDef Sim_methods[] = {
    {"add", (PyCFunction)Sim_add, METH_VARARGS, "Callback this function"},
    {"output", (PyCFunction)Sim_output, METH_VARARGS, "Output something"},
    {NULL}  /* Sentinel */
};

static PyTypeObject SimType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "Sim",
    .tp_basicsize = sizeof(Sim),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_methods = Sim_methods,
    .tp_getattro = Sim_getattr,
};

