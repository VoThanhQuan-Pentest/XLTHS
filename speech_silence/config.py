"""Cấu hình phân khung cố định cho toàn bộ quy trình huấn luyện và kiểm thử."""

# Dùng cùng độ dài khung và bước dịch để so sánh ba thuật toán trên một điều kiện.
FRAME_MS = 25
HOP_MS = 10
FEATURE_LAYOUT = "centered_hop_v1"
TRAINING_PROTOCOL = "train_calibration"
MEDIAN_ORDERS = (1, 5, 9, 11, 15, 21)
HISTOGRAM_WEIGHTS = (1, 2, 5, 10, 15, 20, 30, 50)
