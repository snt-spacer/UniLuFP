#include <micro_ros_arduino.h>
#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/float64_multi_array.h>
#include <FastLED.h>

// --- FastLED Configuration ---
#define NUM_LEDS 32          
#define DATA_PIN 13
#define LED_TYPE WS2811
#define COLOR_ORDER BRG      
CRGB leds[NUM_LEDS];

// --- micro-ROS Configuration ---
#define MAX_ACTUATORS 15     
rcl_subscription_t subscriber;
std_msgs__msg__Float64MultiArray msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

unsigned long last_msg_time = 0;

#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop();}}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}

void error_loop(){
  while(1){
    digitalWrite(2, !digitalRead(2));
    delay(100);
  }
}

const int index_to_led[14] = {
  -1, -1, 14, 17, 6, 9, 30, 1, 22, 25, -1, -1, -1, -1
};

// --- Callback: Runs when ROS 2 message arrives ---
void subscription_callback(const void * msvin) {
  last_msg_time = millis();
  const std_msgs__msg__Float64MultiArray * incoming_msg = (const std_msgs__msg__Float64MultiArray *)msvin;

  fill_solid(leds, NUM_LEDS, CRGB::Black);

  for (size_t i = 0; i < incoming_msg->data.size && i < 14; i++) {
    if (incoming_msg->data.data[i] > 0.01) {
      int led_idx = index_to_led[i];
      if (led_idx != -1 && led_idx < NUM_LEDS) {
        leds[led_idx] = CRGB::Green; 
      }
    }
  }

  if (incoming_msg->data.size > 14) {
    double val_14 = incoming_msg->data.data[14];
    CRGB unmapped_color = CRGB::Black;
    bool active = false;

    if (val_14 > 0.01) { active = true; unmapped_color = CRGB::Blue; }
    else if (val_14 < -0.01) { active = true; unmapped_color = CRGB::Gold; }

    if (active) {
      for (int i = 0; i < NUM_LEDS; i++) {
        // Check if i is one of the mapped indices
        bool is_mapped = (i==14||i==17||i==6||i==9||i==30||i==1||i==22||i==25);
        if (!is_mapped) leds[i] = unmapped_color;
      }
    }
  }
  FastLED.show();
}

void setup() {
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(64); 
  
  set_microros_transports();
  pinMode(2, OUTPUT);

  allocator = rcl_get_default_allocator();

  while (rclc_support_init(&support, 0, NULL, &allocator) != RCL_RET_OK) {
    fill_solid(leds, NUM_LEDS, CRGB::Red); // Visual feedback for "Connecting..."
    FastLED.show();
    delay(100); 
  }

  RCCHECK(rclc_node_init_default(&node, "thruster_led_node", "", &support));

  static double data_buffer[MAX_ACTUATORS];
  msg.data.capacity = MAX_ACTUATORS;
  msg.data.data = data_buffer;

  RCCHECK(rclc_subscription_init_default(
    &subscriber, &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float64MultiArray),
    "/pingu_low_level"));

  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));
  RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA));
  
  fill_solid(leds, NUM_LEDS, CRGB::Black);
  FastLED.show();
}

void loop() {
  // Use 0ms timeout so we don't block the animation frames
  RCSOFTCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(0)));

  // Heartbeat/Idle animation if no ROS messages for 2 seconds
  if (millis() - last_msg_time > 2000) {
    
    // Run the animation logic at a fixed 30ms interval (approx 33 FPS)
    EVERY_N_MILLISECONDS(30) {
      static uint8_t pos = 0;
      static uint8_t hue = 0;

      // 1. Fade the previous trail
      fadeToBlackBy(leds, NUM_LEDS, 60); // Increased fade for a snappier look
      
      // 2. Update position and color
      pos = (pos + 1) % NUM_LEDS;
      hue += 10;
      
      // 3. Draw new lead pixel
      leds[pos] = CHSV(hue, 255, 255);
      
      // 4. Push to hardware
      FastLED.show();
    }
  }
}