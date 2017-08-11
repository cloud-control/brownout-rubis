#ifndef CONTROLLER_H
#define CONTROLLER_H

struct controller_s;
typedef struct controller_s *controller_t;

controller_t controller_init();
void controller_free(controller_t);
void controller_report_arrival(controller_t c);
void controller_report_departure(controller_t c, double response_time, int with_optional);
int controller_with_optional(controller_t c, int current_queue_length);
char *controller_upstream_info(controller_t c);

#endif // CONTROLLER_H
