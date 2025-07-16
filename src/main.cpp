#include "mbed.h"

BufferedSerial pc(USBTX, USBRX, 115200);
CAN can(PA_11, PA_12, (int)1e6);
DigitalIn button(BUTTON1);

int16_t pwm[4] = {0, 0, 0, 0};
bool running = false;

void set_pwm(int16_t value) {
    for (int i = 0; i < 4; i++) pwm[i] = value;
}

int main() {
    char buf[16];
    while (1) {
        // シリアル受信
        if (pc.readable()) {
            int len = pc.read(buf, sizeof(buf) - 1);
            if (len > 0) {
                buf[len] = '\0';
                if (buf[0] == 'i') {
                    running = true;
                } else if (buf[0] == 'o') {
                    running = false;
                } else {
                    int val = atoi(buf);
                    if (val >= -25000 && val <= 25000) {
                        set_pwm(val);
                    }
                }
            }
        }
        // ボタン押下で停止
        if (button == 0) {
            running = false;
        }
        // 動作状態に応じてpwm送信
        int16_t send_pwm[4];
        if (running) {
            for (int i = 0; i < 4; i++) send_pwm[i] = pwm[i];
        } else {
            for (int i = 0; i < 4; i++) send_pwm[i] = 0;
        }
        CANMessage msg(1, (const uint8_t *)send_pwm, 8);
        can.write(msg);
        thread_sleep_for(10);
    }
}