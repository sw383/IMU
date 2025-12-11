# coding:UTF-8
"""
    维特智能传感器数据记录程序 - 时间序列版本 (Epoch时间戳)
    Wit-Motion Sensor Data Recording Program - Time Series Version (Epoch Timestamp)

"""
import os
import time
import datetime
import platform
import struct
import lib.device_model as deviceModel
from lib.data_processor.roles.iwt603_dataProcessor import JY901SDataProcessor
from lib.protocol_resolver.roles.wit_protocol_resolver import WitProtocolResolver

welcome = """
欢迎使用维特智能示例程序 (时间序列版本 - Epoch时间戳)
Welcome to the Wit-Motion sample program (Time Series Version - Epoch Timestamp)
"""

_writeF = None  # 写文件  Write file
_IsWriteF = False  # 写文件标识    Write file identification
SAVE_PATH = r"C:\Users\Shane\Desktop\witdata"  # 数据保存路径

# 时间序列相关变量
_startTime = None  # 记录开始的绝对时间
_sequenceNumber = 0  # 数据序列号
_samplingRate = 0  # 采样率 (Hz)
_lastUpdateTime = None  # 上次更新时间

# 确保目录存在
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)


def readConfig(device):
    """
    读取配置信息示例
    :param device: 设备模型 Device model
    """
    tVals = device.readReg(0x02, 3)
    if tVals:
        print("返回结果：" + str(tVals))
    else:
        print("无返回")
    tVals = device.readReg(0x23, 2)
    if tVals:
        print("返回结果：" + str(tVals))
    else:
        print("无返回")


def setConfig(device):
    """
    设置配置信息示例
    :param device: 设备模型 Device model
    """
    device.unlock()
    time.sleep(0.1)
    device.writeReg(0x03, 6)
    time.sleep(0.1)
    device.writeReg(0x23, 0)
    time.sleep(0.1)
    device.writeReg(0x24, 0)
    time.sleep(0.1)
    device.save()


def AccelerationCalibration(device):
    """
    加计校准
    :param device: 设备模型 Device model
    """
    device.AccelerationCalibration()
    print("加计校准结束")


def FiledCalibration(device):
    """
    磁场校准
    :param device: 设备模型 Device model
    """
    device.BeginFiledCalibration()
    if input("请分别绕XYZ轴慢速转动一圈，三轴转圈完成后，结束校准（Y/N)？").lower() == "y":
        device.EndFiledCalibration()
        print("结束磁场校准")


def onUpdate(deviceModel):
    """
    数据更新事件 - 时间序列版本 (Epoch时间戳)
    :param deviceModel: 设备模型
    """
    global _writeF, _IsWriteF, _startTime, _sequenceNumber, _samplingRate, _lastUpdateTime

    # 获取当前 epoch 时间戳（秒，保留微秒精度）
    current_time = time.time()
    current_datetime = datetime.datetime.now()

    # 计算相对时间（从开始记录起的秒数）
    if _startTime is not None:
        relative_time = current_time - _startTime
    else:
        relative_time = 0.0

    # 计算实时采样率
    if _lastUpdateTime is not None:
        time_diff = current_time - _lastUpdateTime
        if time_diff > 0:
            instant_rate = 1.0 / time_diff
            # 使用移动平均来平滑采样率
            _samplingRate = 0.9 * _samplingRate + 0.1 * instant_rate
    _lastUpdateTime = current_time

    temperature = deviceModel.getDeviceData("temperature") or 0.0

    # 格式化显示时间（便于阅读）
    time_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    print(f"序号:{_sequenceNumber:06d}"
          f" Epoch:{current_time:.6f}"
          f" 相对:{relative_time:.3f}s"
          f" [{time_str}]"
          f" 温度:{temperature:.2f}"
          f" 加速度:({deviceModel.getDeviceData('accX') or 0:.4f},"
          f"{deviceModel.getDeviceData('accY') or 0:.4f},"
          f"{deviceModel.getDeviceData('accZ') or 0:.4f})"
          f" 角速度:({deviceModel.getDeviceData('gyroX') or 0:.4f},"
          f"{deviceModel.getDeviceData('gyroY') or 0:.4f},"
          f"{deviceModel.getDeviceData('gyroZ') or 0:.4f})"
          f" 角度:({deviceModel.getDeviceData('angleX') or 0:.2f},"
          f"{deviceModel.getDeviceData('angleY') or 0:.2f},"
          f"{deviceModel.getDeviceData('angleZ') or 0:.2f})"
          f" 采样率:{_samplingRate:.1f}Hz"
          )

    if _IsWriteF:
        # 写入时间序列数据，使用 epoch 时间戳，使用逗号 "," 分隔
        data_row = f"{_sequenceNumber},{current_time:.6f},{relative_time:.6f},"
        data_row += ",".join([str(deviceModel.getDeviceData(k) or 0) for k in [
            "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ",
            "angleX", "angleY", "angleZ", "temperature",
            "magX", "magY", "magZ", "lon", "lat",
            "Yaw", "Speed", "q1", "q2", "q3", "q4"
        ]])
        data_row += "\r\n"
        _writeF.write(data_row)

        _sequenceNumber += 1


def startRecord():
    """
    开始记录数据
    """
    global _writeF, _IsWriteF, _startTime, _sequenceNumber, _samplingRate, _lastUpdateTime

    _startTime = time.time()
    _sequenceNumber = 0
    _samplingRate = 0
    _lastUpdateTime = None

    start_datetime = datetime.datetime.now()
    # 文件名格式: YYYYMMDDHHMMSSmmm_timeseries_epoch.csv
    filename = start_datetime.strftime('%Y%m%d%H%M%S%f')[:-3] + "_timeseries_epoch.csv"
    filepath = os.path.join(SAVE_PATH, filename)
    _writeF = open(filepath, "w", encoding="utf-8")
    _IsWriteF = True

    # 写入文件头信息
    _writeF.write(f"# 维特智能传感器数据文件 - 时间序列格式 (Epoch时间戳)\n")
    _writeF.write(f"# Wit-Motion Sensor Data File - Time Series Format (Epoch Timestamp)\n")
    _writeF.write(f"# 开始时间 Start Time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
    _writeF.write(f"# 开始时间戳 Start Epoch: {_startTime:.6f}\n")
    _writeF.write(f"# 时间格式说明 Timestamp Format: Unix Epoch (seconds since 1970-01-01 00:00:00 UTC)\n")
    _writeF.write(f"# ================================\n")

    # 写入列标题 - 使用逗号 "," 分隔
    header = "Sequence,EpochTime(s),RelativeTime(s),"
    header += "ax(g),ay(g),az(g),wx(deg/s),wy(deg/s),wz(deg/s),"
    header += "AngleX(deg),AngleY(deg),AngleZ(deg),T(°),"
    header += "magx,magy,magz,lon,lat,Yaw,Speed,q1,q2,q3,q4\r\n"
    _writeF.write(header)

    print(f"\n开始记录数据")
    print(f"保存路径: {filepath}")
    print(f"开始时间: {start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"Epoch时间戳: {_startTime:.6f}")
    print(f"时间格式: Unix Epoch (秒，保留6位小数)")
    print("=" * 80)


def endRecord():
    """
    结束记录数据
    """
    global _writeF, _IsWriteF, _startTime, _sequenceNumber, _samplingRate

    end_time = time.time()
    end_datetime = datetime.datetime.now()

    if _IsWriteF and _writeF:
        # 写入结束信息
        duration = end_time - _startTime if _startTime else 0
        avg_rate = _sequenceNumber / duration if duration > 0 else 0

        _writeF.write(f"\n# ================================\n")
        _writeF.write(f"# 结束时间 End Time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
        _writeF.write(f"# 结束时间戳 End Epoch: {end_time:.6f}\n")
        _writeF.write(f"# 记录时长 Duration: {duration:.3f} seconds\n")
        _writeF.write(f"# 数据点数 Data Points: {_sequenceNumber}\n")
        _writeF.write(f"# 平均采样率 Average Sampling Rate: {avg_rate:.2f} Hz\n")

        _IsWriteF = False
        _writeF.close()

        print("\n" + "=" * 80)
        print("结束记录数据")
        print(f"记录时长: {duration:.3f} 秒")
        print(f"数据点数: {_sequenceNumber}")
        print(f"平均采样率: {avg_rate:.2f} Hz")


if __name__ == '__main__':
    print(welcome)

    device = deviceModel.DeviceModel(
        "我的iwt603",
        WitProtocolResolver(),
        JY901SDataProcessor(),
        "51_0"
    )

    # 配置串口
    if platform.system().lower() == 'linux':
        device.serialConfig.portName = "/dev/ttyUSB0"
    else:
        device.serialConfig.portName = "COM3"
    device.serialConfig.baud = 921600

    print("正在打开设备...")
    device.openDevice()

    print("等待设备初始化...")
    time.sleep(1)

    # 读取配置（可选）
    # readConfig(device)

    # 注册数据更新回调
    device.dataProcessor.onVarChanged.append(onUpdate)

    # 开始记录
    startRecord()

    print("\n按 Enter 键停止记录...")
    input()

    # 停止记录并关闭设备
    device.closeDevice()
    endRecord()

    print("\n程序结束")