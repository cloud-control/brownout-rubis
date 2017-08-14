#include "controller.h"

#include <stdlib.h>
#include <stdio.h>

#include <Python.h>

static double now()
{
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return ts.tv_nsec / 1000000000.0 + ts.tv_sec;
}

#define LOG(level, fmt, ...) fprintf(stderr, "[%lf][%s][%s] " fmt "\n", now(), __FUNCTION__, level, ##__VA_ARGS__)

#define LOG_INFO(fmt, ...)  LOG("info", fmt, ##__VA_ARGS__)
#define LOG_WARN(fmt, ...)  LOG("warn", fmt, ##__VA_ARGS__)
#define LOG_ERROR(fmt, ...) LOG("error", fmt, ##__VA_ARGS__)

struct controller_s {
    PyObject *pController;
};

#define ABORT_WITH_PYERR(fmt, ...) \
    do { \
        if (PyErr_Occurred()) \
            PyErr_Print(); \
        LOG_ERROR(fmt, ##__VA_ARGS__); \
        exit(1); \
    } while(0)

controller_t controller_init() {
    controller_t c = malloc(sizeof(struct controller_s));
    char fake_argv[] = { "" };

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
        "args = parser.parse_args()\n"
        "controllerModule.parseCommandLine(args)\n"
    );

    PyObject *pNewInstance = PyObject_GetAttrString(pModule, "newInstance");
    if (pNewInstance == 0)
        ABORT_WITH_PYERR("Could not find newInstance in Python controller; aborting");
    Py_DECREF(pModule);

    if (PyCallable_Check(pNewInstance) == 0)
        ABORT_WITH_PYERR("newInstance in Python controller is not callable; aborting");

    PyObject *pArgs = PyTuple_New(2);
    PyTuple_SetItem(pArgs, 0, Py_None);
    PyTuple_SetItem(pArgs, 1, Py_None);
    c->pController = PyObject_CallObject(pNewInstance, pArgs);
    Py_DECREF(pArgs);
    Py_DECREF(pNewInstance);

    if (c->pController == 0)
        ABORT_WITH_PYERR("Could not create new instance of controller; aborting");

    return c;
}

void controller_free(controller_t c) {
    Py_Finalize();

    free(c);
}

void controller_report_arrival(controller_t c) {
}

void controller_report_departure(controller_t c, double response_time, int with_optional) {
}

int controller_with_optional(controller_t c, int current_queue_length) {
    return current_queue_length <= 5;
}

char *controller_upstream_info(controller_t c) {
    return "5";
}

void controller_run_control_loop(controller_t c) {
    fprintf(stderr, "%s\n", __FUNCTION__);
}
