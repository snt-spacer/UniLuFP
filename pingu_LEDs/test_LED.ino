#define FASTLED_ALLOW_INTERRUPTS 0
#include <FastLED.h>

#define NUM_LEDS 33      // Total number of addressable units
#define DATA_PIN 13      // The GPIO pin on your ESP32
#define LED_TYPE WS2811
#define COLOR_ORDER BRG

CRGB leds[NUM_LEDS];

void setup() {
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS);
}

void loop() {

  // Turn everything else off
  for(int i = 0; i < NUM_LEDS; i++) {
    leds[i] = CRGB::Pink;
  }

  leds[0] = CRGB::Red;
  leds[32] = CRGB::Tomato;

  FastLED.show();
  delay(1000);
}