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

#define LOG_ERROR(fmt, ...) LOG("error", fmt, ##__VA_ARGS__)

struct controller_s {
    PyObject *pModule;
};

controller_t controller_init() {
    controller_t c = malloc(sizeof(struct controller_s));

    Py_Initialize();
    PyObject *pName = PyString_FromString("cf_cascaded.py");
    c->pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (c->pModule == 0)
        LOG_ERROR("Could not load Python module; controller disabled");

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
    if (!c->pModule) return;
    fprintf(stderr, "%s\n", __FUNCTION__);
}
