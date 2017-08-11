#include "controller.h"

#include <stdlib.h>

struct controller_s {
    int unused_yet;
};

controller_t controller_init() {
    controller_t c = malloc(sizeof(struct controller_s));
    c->unused_yet = 0;
    return c;
}

void controller_free(controller_t c) {
    free(c);
}

void controller_report_arrival(controller_t c) {
}

void controller_report_departure(controller_t c, double response_time, int with_optional) {
}

int controller_with_optional(controller_t c, int current_queue_length) {
    return current_queue_length <= 5;
}
