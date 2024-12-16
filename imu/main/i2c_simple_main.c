#include <stdio.h>
#include "driver/i2c.h"
#include "mpu6050.h"
#include "esp_system.h"
#include "esp_log.h"

#define I2C_MASTER_SCL_IO 1
#define I2C_MASTER_SDA_IO 0
#define I2C_MASTER_NUM I2C_NUM_0
#define I2C_MASTER_FREQ_HZ 100000

static const char *TAG = "mpu6050";
static mpu6050_handle_t mpu6050 = NULL;

static void i2c_bus_init(void)
{
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ
    };

    esp_err_t ret = i2c_param_config(I2C_MASTER_NUM, &conf);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C param config failed: %s", esp_err_to_name(ret));
        return;
    }

    ret = i2c_driver_install(I2C_MASTER_NUM, conf.mode, 0, 0, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C driver install failed: %s", esp_err_to_name(ret));
        return;
    }
}

static void i2c_sensor_mpu6050_init(void)
{
    i2c_bus_init();
    mpu6050 = mpu6050_create(I2C_MASTER_NUM, MPU6050_I2C_ADDRESS);
    if (mpu6050 == NULL) {
        ESP_LOGE(TAG, "Failed to create MPU6050 instance");
        esp_restart();
    }
    mpu6050_config(mpu6050, ACCE_FS_4G, GYRO_FS_500DPS);
    mpu6050_wake_up(mpu6050);
}

void app_main()
{
    i2c_sensor_mpu6050_init();

    const int delay_ms = 10; 
    const int data_collection_time = 4 * 1000 / delay_ms;

    while (true) { 
        printf("Waiting 4 seconds before starting data collection...\n");
        fflush(stdout);
        vTaskDelay(4000 / portTICK_PERIOD_MS);

        // Start data collection
        printf("START\n");
        fflush(stdout); 

        for (int i = 0; i < data_collection_time; i++) {
            mpu6050_acce_value_t acce;
            mpu6050_gyro_value_t gyro;

            mpu6050_get_acce(mpu6050, &acce);
            mpu6050_get_gyro(mpu6050, &gyro);

            printf("%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n", 
                (i * delay_ms) / 1000.0,
                acce.acce_x, acce.acce_y, acce.acce_z, 
                gyro.gyro_x, gyro.gyro_y, gyro.gyro_z);
            fflush(stdout); 

            vTaskDelay(delay_ms / portTICK_PERIOD_MS);
        }

        printf("END\n");
        fflush(stdout); 

        // Wait 4 seconds before the next measurement
        printf("Waiting 4 seconds before the next cycle...\n");
        fflush(stdout);
        vTaskDelay(4000 / portTICK_PERIOD_MS); 
    }
}
