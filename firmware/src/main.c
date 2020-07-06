#include "mgos.h"
#include "mgos_i2c.h"
#include "mgos_mqtt.h"

enum {
  ERROR_UNKNOWN_COMMAND = -1,
};

static void init_pixel() {
  uint8_t stopScrptCmd[] = {0x6f};
  struct mgos_i2c *i2c = mgos_i2c_get_global();
  mgos_i2c_write(i2c, 0x09, stopScrptCmd, 1, true);
  mgos_msleep(100);
}

static void set_color(int red, int green, int blue) {
  init_pixel();
  uint8_t colorCmd[] = {0x6e, 0x00, 0x00, 0x00};
  colorCmd[1] = red;
  colorCmd[2] = green;
  colorCmd[3] = blue;

  struct mgos_i2c *i2c = mgos_i2c_get_global();
  mgos_i2c_write(i2c, 0x09, colorCmd, 4, true);
}

static void sub(struct mg_connection *c, const char *fmt, ...) {
  char buf[100];
  struct mg_mqtt_topic_expression te = {.topic = buf, .qos = 1};
  uint16_t sub_id = mgos_mqtt_get_packet_id();
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(buf, sizeof(buf), fmt, ap);
  va_end(ap);
  mg_mqtt_subscribe(c, &te, 1, sub_id);
  LOG(LL_INFO, ("Subscribing to %s (id %u)", buf, sub_id));
}

static void pub(struct mg_connection *c, const char *fmt, ...) {
  char msg[200];
  struct json_out jmo = JSON_OUT_BUF(msg, sizeof(msg));
  va_list ap;
  int n;
  va_start(ap, fmt);
  n = json_vprintf(&jmo, fmt, ap);
  va_end(ap);
  mg_mqtt_publish(c, mgos_sys_config_get_mqtt_pub(), mgos_mqtt_get_packet_id(),
                  MG_MQTT_QOS(1), msg, n);
  LOG(LL_INFO, ("%s -> %s", mgos_sys_config_get_mqtt_pub(), msg));
}

static void ev_handler(struct mg_connection *c, int ev, void *p,
                       void *user_data) {
  struct mg_mqtt_message *msg = (struct mg_mqtt_message *) p;

  if (ev == MG_EV_MQTT_CONNACK) {
    LOG(LL_INFO, ("CONNACK: %d", msg->connack_ret_code));
    if (mgos_sys_config_get_mqtt_sub() == NULL ||
        mgos_sys_config_get_mqtt_pub() == NULL) {
      LOG(LL_ERROR, ("Run 'mgos config-set mqtt.sub=... mqtt.pub=...'"));
    } else {
      sub(c, "%s", mgos_sys_config_get_mqtt_sub());
    }
  } else if (ev == MG_EV_MQTT_SUBACK) {
    LOG(LL_INFO, ("Subscription %u acknowledged", msg->message_id));
  } else if (ev == MG_EV_MQTT_PUBLISH) {
    struct mg_str *s = &msg->payload;
    int red, green, blue = 0;
    const char *timestamp;

    LOG(LL_INFO, ("got command: [%.*s]", (int) s->len, s->p));
    /* Our subscription is at QoS 1, we must acknowledge messages sent ot us. */
    mg_mqtt_puback(c, msg->message_id);
    int scan_result =
        json_scanf(s->p, s->len, "{time: %Q, red: %d, green: %d, blue: %d }",
                   &timestamp, &red, &green, &blue);
    LOG(LL_INFO, ("scan_result: %d", scan_result));

    if (scan_result >= 2) {
      char msg[300];
      struct json_out jmo = JSON_OUT_BUF(msg, sizeof(msg));

      set_color(red, green, blue);
      json_printf(&jmo,
                  "{ timestamp: \"%s\", "
                  "red: %d, green: %d, blue: %d}",
                  timestamp, red, green, blue);
      pub(c, "%s", msg);
    } else {
      pub(c, "{error: {code: %d, message: %Q}}", ERROR_UNKNOWN_COMMAND,
          "unknown command");
    }
  }
  (void) user_data;
}

enum mgos_app_init_result mgos_app_init(void) {
  init_pixel();
  set_color(0, 255, 0); // init to green 
  mgos_mqtt_add_global_handler(ev_handler, NULL);
  return MGOS_APP_INIT_SUCCESS;
}
