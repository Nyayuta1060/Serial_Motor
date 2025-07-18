#include "mbed.h"

BufferedSerial pc(USBTX, USBRX, 115200);
CAN can(PA_11, PA_12, (int)1e6);
DigitalIn button(BUTTON1);

int16_t pwm[4] = {0, 0, 0, 0};
bool running = false;
uint32_t can_id = 1;  // デフォルトCAN ID

void set_pwm(int16_t value) {
    for (int i = 0; i < 4; i++) pwm[i] = value;
}

void set_individual_pwm(int index, int16_t value) {
    if (index >= 0 && index < 4) {
        pwm[index] = value;
    }
}

void parse_pwm_command(const char* cmd) {
    char* cmd_copy = new char[strlen(cmd) + 1];
    strcpy(cmd_copy, cmd);
    
    char* token = strtok(cmd_copy, ",");
    while (token != nullptr) {
        if (token[0] == 'p' && token[1] >= '0' && token[1] <= '3' && token[2] == ':') {
            int index = token[1] - '0';
            int value = atoi(&token[3]);
            if (value >= -25000 && value <= 25000) {
                set_individual_pwm(index, value);
            }
        }
        token = strtok(nullptr, ",");
    }
    
    delete[] cmd_copy;
}

int main() {
    char buf[64];  // バッファサイズを増加
    while (1) {
        // シリアル受信
        if (pc.readable()) {
            int len = pc.read(buf, sizeof(buf) - 1);
            if (len > 0) {
                buf[len] = '\0';
                
                if (buf[len-1] == '\n' || buf[len-1] == '\r') {
                    buf[len-1] = '\0';
                }
                
                if (buf[0] == 'i') {
                    running = true;
                } else if (buf[0] == 'o') {
                    running = false;
                } else if (buf[0] == 'c') {
                    // CAN ID設定
                    int new_can_id = atoi(&buf[1]);
                    if (new_can_id >= 1 && new_can_id <= 4) {
                        can_id = new_can_id;
                    }
                } else if (buf[0] == 'p') {
                    // 個別PWM設定
                    parse_pwm_command(buf);
                } else {
                    // 一括PWM設定
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
        int16_t send_pwm[4];
        if (running) {
            for (int i = 0; i < 4; i++) send_pwm[i] = pwm[i];
        } else {
            for (int i = 0; i < 4; i++) send_pwm[i] = 0;
        }
        CANMessage msg(can_id, (const uint8_t *)send_pwm, 8);
        can.write(msg);
        thread_sleep_for(10);
    }
}