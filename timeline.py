import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.ndimage import gaussian_filter1d

# Dataset 1 - your original timestamps
timestamps1 = [
    "2025-01-25 16:17", "2025-01-25 18:53", "2025-01-30 20:25", "2025-01-30 20:28",
    "2025-02-18 03:12", "2025-02-18 19:13", "2025-02-20 02:16", "2025-02-20 13:38", 
    "2025-02-20 23:59", "2025-02-21 08:30", "2025-02-21 11:04", "2025-02-21 14:01", 
    "2025-02-21 18:12", "2025-02-21 19:18", "2025-02-21 21:39", "2025-02-22 14:17",
    "2025-02-22 16:48", "2025-02-22 16:57", "2025-02-23 19:51", "2025-02-23 19:54", 
    "2025-02-24 03:43", "2025-02-24 04:18", "2025-02-24 04:24", "2025-02-24 10:19", 
    "2025-02-24 12:07", "2025-02-24 12:44", "2025-02-24 13:03", "2025-02-24 13:53", 
    "2025-02-24 14:19", "2025-02-24 16:43", "2025-02-24 16:49", "2025-02-24 17:27", 
    "2025-02-24 17:32", "2025-02-24 19:17", "2025-02-24 19:39", "2025-02-24 19:46", 
    "2025-02-24 20:15", "2025-02-24 21:45", "2025-02-25 03:31", "2025-02-25 03:59", 
    "2025-02-26 10:40", "2025-03-09 12:20", "2025-03-09 14:11", "2025-03-09 17:47", 
    "2025-03-10 05:25", "2025-03-10 10:18", "2025-03-10 11:12", "2025-03-10 14:00", 
    "2025-03-10 17:03", "2025-03-10 20:18", "2025-03-11 00:41", "2025-03-11 01:23", 
    "2025-03-11 02:11", "2025-03-11 04:31", "2025-03-11 10:26"
]

# Dataset 2 - new timestamps (assuming 2024 for Nov/Dec, 2025 for Jan)
timestamps2 = [
    "2024-11-27 12:58", "2024-11-28 10:16", "2024-11-29 12:30", "2024-12-03 17:52",
    "2024-12-03 21:40", "2024-12-04 14:52", "2024-12-19 02:12", "2024-12-19 02:42",
    "2024-12-19 03:02", "2024-12-19 04:59", "2024-12-19 13:09", "2024-12-19 21:11",
    "2024-12-19 22:38", "2024-12-22 20:47", "2025-01-07 13:28", "2025-01-08 14:23",
    "2025-01-11 10:56", "2025-01-11 18:03", "2025-01-11 19:12", "2025-01-11 22:29",
    "2025-01-12 08:56", "2025-01-12 09:36", "2025-01-12 09:44", "2025-01-12 09:53",
    "2025-01-12 10:55", "2025-01-12 11:00", "2025-01-12 16:23", "2025-01-12 16:57",
    "2025-01-12 17:06", "2025-01-13 22:56", "2025-01-23 18:35"
]

# Dataset 3 - third timestamps (assuming 2024 for Dec, 2025 for Feb-May)
timestamps3 = [
    "2024-12-28 14:43", "2025-02-10 03:02", "2025-02-20 03:57", "2025-02-20 08:40",
    "2025-03-19 08:53", "2025-03-26 08:51", "2025-04-03 06:01", "2025-04-03 08:10",
    "2025-04-03 10:20", "2025-04-07 07:20", "2025-04-23 21:05", "2025-04-29 06:56",
    "2025-05-01 07:04", "2025-05-03 07:19", "2025-05-04 09:52", "2025-05-09 22:45",
    "2025-05-11 06:03", "2025-05-12 07:16", "2025-05-12 17:39", "2025-05-13 13:57",
    "2025-05-14 01:23", "2025-05-14 04:02", "2025-05-14 20:53", "2025-05-15 21:59",
    "2025-05-16 13:43", "2025-05-16 13:59", "2025-05-17 15:57", "2025-05-19 00:15",
    "2025-05-20 04:50", "2025-05-20 17:38", "2025-05-20 20:37", "2025-05-22 11:15",
    "2025-05-22 20:04", "2025-05-22 21:50", "2025-05-23 09:47", "2025-05-24 21:49",
    "2025-05-25 03:02", "2025-05-25 11:50", "2025-05-25 17:48", "2025-05-25 20:37",
    "2025-05-26 01:59", "2025-05-26 06:29", "2025-05-26 09:35", "2025-05-26 13:41",
    "2025-05-26 15:59", "2025-05-26 21:24", "2025-05-26 22:06", "2025-05-27 01:47",
    "2025-05-27 02:17", "2025-05-27 06:49", "2025-05-27 12:51", "2025-05-27 13:04",
    "2025-05-27 13:21", "2025-05-27 14:15", "2025-05-27 14:59", "2025-05-27 16:28",
    "2025-05-27 17:10", "2025-05-27 17:15", "2025-05-27 19:12", "2025-05-27 19:29",
    "2025-05-27 19:36", "2025-05-27 19:48", "2025-05-27 19:58", "2025-05-27 19:59",
    "2025-05-27 20:01", "2025-05-27 20:03", "2025-05-27 20:18", "2025-05-27 20:59",
    "2025-05-27 21:08", "2025-05-27 21:29", "2025-05-27 21:30", "2025-05-27 21:33",
    "2025-05-27 21:55", "2025-05-27 21:57", "2025-05-27 22:02", "2025-05-27 23:29",
    "2025-05-28 01:09", "2025-05-28 02:01", "2025-05-28 02:13", "2025-05-28 02:18",
    "2025-05-28 03:11", "2025-05-28 03:12", "2025-05-28 03:35", "2025-05-28 03:54",
    "2025-05-28 04:06", "2025-05-28 04:57", "2025-05-28 05:07", "2025-05-28 06:07",
    "2025-05-28 06:16", "2025-05-28 06:54", "2025-05-28 07:06", "2025-05-28 10:30",
    "2025-05-28 10:58", "2025-05-28 11:19", "2025-05-28 11:58", "2025-05-28 12:01",
    "2025-05-28 12:11", "2025-05-28 13:35"
]

# Dataset 4 - fourth timestamps (assuming 2025 for all Jan-Mar dates)
timestamps4 = [
    "2025-01-03 20:00", "2025-01-08 16:44", "2025-01-13 06:18", "2025-01-20 18:41",
    "2025-01-20 18:50", "2025-01-20 18:54", "2025-01-21 20:53", "2025-01-24 12:27",
    "2025-01-24 12:49", "2025-01-24 15:12", "2025-01-25 11:45", "2025-01-27 11:52",
    "2025-02-07 14:55", "2025-02-13 17:11", "2025-02-17 05:34", "2025-02-18 04:59",
    "2025-02-18 09:01", "2025-02-18 09:21", "2025-02-18 12:24", "2025-02-19 12:22",
    "2025-02-19 17:11", "2025-02-19 17:31", "2025-02-20 04:46", "2025-02-20 11:53",
    "2025-02-20 17:28", "2025-02-20 19:13", "2025-02-20 19:23", "2025-02-20 20:58",
    "2025-02-21 00:37", "2025-02-21 03:57", "2025-02-21 04:29", "2025-02-21 05:58",
    "2025-02-21 06:01", "2025-02-21 06:01", "2025-02-21 07:11", "2025-02-21 07:38",
    "2025-02-21 09:55", "2025-02-21 10:42", "2025-02-21 10:45", "2025-02-21 11:29",
    "2025-02-21 14:05", "2025-02-21 16:35", "2025-02-21 17:58", "2025-02-21 18:08",
    "2025-02-21 18:59", "2025-02-21 20:04", "2025-02-22 03:53", "2025-02-22 13:18",
    "2025-02-22 21:47", "2025-02-23 04:06", "2025-02-23 06:25", "2025-02-23 08:59",
    "2025-02-23 10:49", "2025-02-23 10:52", "2025-02-23 12:54", "2025-02-23 13:22",
    "2025-02-23 16:10", "2025-02-23 16:54", "2025-02-23 17:56", "2025-02-23 18:28",
    "2025-02-23 19:05", "2025-02-23 20:56", "2025-02-23 21:24", "2025-02-23 21:49",
    "2025-02-23 22:20", "2025-02-23 23:09", "2025-02-24 00:07", "2025-02-24 00:33",
    "2025-02-24 01:52", "2025-02-24 04:03", "2025-02-24 04:32", "2025-02-24 04:41",
    "2025-02-24 04:45", "2025-02-24 04:51", "2025-02-24 05:46", "2025-02-24 05:49",
    "2025-02-24 06:57", "2025-02-24 07:41", "2025-02-24 07:55", "2025-02-24 09:29",
    "2025-02-24 10:23", "2025-02-24 10:39", "2025-02-24 10:41", "2025-02-24 10:45",
    "2025-02-24 11:59", "2025-02-24 12:07", "2025-02-24 12:11", "2025-02-24 12:19",
    "2025-02-24 12:38", "2025-02-24 13:23", "2025-02-24 13:55", "2025-02-24 13:59",
    "2025-02-24 14:03", "2025-02-24 14:04", "2025-02-24 14:08", "2025-02-24 14:09",
    "2025-02-24 14:36", "2025-02-24 14:39", "2025-02-24 15:15", "2025-02-24 15:24",
    "2025-02-24 15:25", "2025-02-24 15:27", "2025-02-24 15:29", "2025-02-24 15:45",
    "2025-02-24 16:34", "2025-02-24 16:50", "2025-02-24 17:35", "2025-02-24 17:57",
    "2025-02-24 17:57", "2025-02-24 18:38", "2025-02-24 18:57", "2025-02-24 19:13",
    "2025-02-24 19:18", "2025-02-24 19:40", "2025-02-24 19:50", "2025-02-24 19:56",
    "2025-02-24 20:25", "2025-02-24 22:47", "2025-02-24 22:53", "2025-02-24 23:04",
    "2025-02-24 23:31", "2025-02-25 00:33", "2025-02-25 02:20", "2025-02-25 02:58",
    "2025-02-25 03:29", "2025-02-25 04:09", "2025-02-25 04:37", "2025-02-25 05:20",
    "2025-02-25 05:44", "2025-02-25 05:45", "2025-02-25 06:02", "2025-02-25 07:47",
    "2025-02-25 09:45", "2025-02-25 10:26", "2025-02-25 15:25", "2025-02-25 17:07",
    "2025-02-28 05:13", "2025-02-28 10:01", "2025-02-28 19:02", "2025-03-01 02:24",
    "2025-03-01 19:29", "2025-03-02 03:08", "2025-03-04 02:03", "2025-03-04 05:04",
    "2025-03-04 15:30", "2025-03-04 18:01", "2025-03-06 05:56", "2025-03-06 07:16",
    "2025-03-06 16:51", "2025-03-07 08:37", "2025-03-07 11:02", "2025-03-08 23:11",
    "2025-03-09 09:44", "2025-03-09 19:10", "2025-03-09 23:35", "2025-03-10 04:10",
    "2025-03-10 07:22", "2025-03-10 08:43", "2025-03-10 09:53", "2025-03-10 12:45",
    "2025-03-10 13:00", "2025-03-10 13:36", "2025-03-10 16:05", "2025-03-10 17:48",
    "2025-03-10 17:58", "2025-03-10 18:01", "2025-03-10 19:59", "2025-03-10 20:31",
    "2025-03-10 20:37", "2025-03-10 20:57", "2025-03-10 23:10", "2025-03-11 01:08",
    "2025-03-11 01:13", "2025-03-11 02:07", "2025-03-11 03:09", "2025-03-11 04:08",
    "2025-03-11 04:41", "2025-03-11 06:46", "2025-03-11 08:06", "2025-03-11 08:07",
    "2025-03-11 08:27", "2025-03-11 09:40", "2025-03-11 10:26", "2025-03-11 10:53",
    "2025-03-11 10:54"
]

# Dataset 5 - fifth timestamps (assuming 2024 for Aug-Sep dates)
timestamps5 = [
    "2024-08-01 10:50", "2024-08-04 15:35", "2024-08-04 15:36", "2024-08-05 04:04",
    "2024-08-06 22:11", "2024-08-08 14:15", "2024-08-09 01:45", "2024-08-15 20:16",
    "2024-08-21 15:25", "2024-08-22 09:51", "2024-08-27 05:52", "2024-08-27 08:04",
    "2024-09-01 17:10", "2024-09-02 15:42", "2024-09-02 20:05", "2024-09-02 20:12",
    "2024-09-03 04:38", "2024-09-03 07:42", "2024-09-03 11:52", "2024-09-03 14:22",
    "2024-09-03 14:27", "2024-09-03 14:32", "2024-09-03 15:32", "2024-09-04 15:42",
    "2024-09-04 17:34", "2024-09-04 21:10", "2024-09-04 23:24", "2024-09-05 11:44",
    "2024-09-05 16:32", "2024-09-05 20:12", "2024-09-05 20:15", "2024-09-10 06:40",
    "2024-09-11 07:24", "2024-09-11 12:53", "2024-09-11 15:26", "2024-09-12 11:23",
    "2024-09-16 06:50", "2024-09-16 13:15", "2024-09-17 01:24", "2024-09-17 02:23",
    "2024-09-17 10:49", "2024-09-17 11:32", "2024-09-17 15:08", "2024-09-17 16:56",
    "2024-09-17 18:28", "2024-09-18 09:49", "2024-09-18 11:57", "2024-09-18 13:20",
    "2024-09-18 13:39", "2024-09-18 14:43", "2024-09-18 14:55", "2024-09-18 15:22",
    "2024-09-19 00:34", "2024-09-19 02:38", "2024-09-19 08:30", "2024-09-19 12:05",
    "2024-09-19 12:16", "2024-09-19 12:45", "2024-09-19 13:02", "2024-09-19 13:26",
    "2024-09-19 13:44", "2024-09-19 13:55", "2024-09-19 14:16", "2024-09-19 15:28",
    "2024-09-19 16:52", "2024-09-19 18:31", "2024-09-19 20:37", "2024-09-19 21:14",
    "2024-09-19 21:23", "2024-09-19 21:48", "2024-09-19 22:00", "2024-09-19 22:01",
    "2024-09-19 23:03", "2024-09-19 23:15", "2024-09-20 03:29", "2024-09-20 11:00",
    "2024-09-20 11:21", "2024-09-20 11:33", "2024-09-20 11:41", "2024-09-20 11:58",
    "2024-09-20 12:03"
]

# Dataset 6 - sixth timestamps (assuming 2024 for Dec, 2025 for Jan)
timestamps6 = [
    "2024-12-11 11:01", "2024-12-15 07:50", "2024-12-21 08:24", "2024-12-25 08:59",
    "2024-12-27 02:49", "2024-12-30 12:49", "2025-01-03 05:39", "2025-01-04 06:43",
    "2025-01-04 15:11", "2025-01-04 23:16", "2025-01-05 15:28", "2025-01-07 20:53",
    "2025-01-08 08:04", "2025-01-09 06:13", "2025-01-10 01:05", "2025-01-10 01:09",
    "2025-01-10 14:03", "2025-01-10 19:06", "2025-01-11 00:57", "2025-01-11 02:58",
    "2025-01-11 04:06", "2025-01-11 04:13", "2025-01-11 06:31", "2025-01-11 06:31",
    "2025-01-11 06:32", "2025-01-11 06:32", "2025-01-11 08:06", "2025-01-11 08:39",
    "2025-01-11 09:16", "2025-01-11 09:22", "2025-01-11 10:34", "2025-01-11 12:51",
    "2025-01-11 13:36", "2025-01-11 13:37", "2025-01-11 13:47", "2025-01-11 15:55",
    "2025-01-11 16:14", "2025-01-11 18:23", "2025-01-11 18:36", "2025-01-11 19:40",
    "2025-01-12 03:48", "2025-01-12 03:50", "2025-01-12 04:35", "2025-01-12 04:36",
    "2025-01-12 09:50", "2025-01-12 10:21", "2025-01-12 12:38", "2025-01-12 12:51",
    "2025-01-12 13:28", "2025-01-12 13:39", "2025-01-12 13:45", "2025-01-12 14:12",
    "2025-01-12 14:14", "2025-01-12 14:55", "2025-01-12 16:19", "2025-01-12 18:45",
    "2025-01-12 20:04", "2025-01-12 20:45", "2025-01-13 00:31", "2025-01-13 03:48",
    "2025-01-17 04:01"
]

# Dataset 7 - seventh timestamps (assuming 2025 for Apr-May dates)
timestamps7 = [
    "2025-04-18 02:26", "2025-04-19 00:42", "2025-04-19 09:34", "2025-04-22 20:02",
    "2025-04-30 08:11", "2025-05-01 12:14", "2025-05-02 21:18", "2025-05-03 03:36",
    "2025-05-03 07:44", "2025-05-06 07:30", "2025-05-08 15:00", "2025-05-09 09:32",
    "2025-05-14 07:58", "2025-05-16 09:15", "2025-05-22 06:57", "2025-05-22 19:18",
    "2025-05-23 15:08", "2025-05-24 00:32", "2025-05-24 08:32", "2025-05-25 03:39",
    "2025-05-25 20:56", "2025-05-26 01:41", "2025-05-26 09:13", "2025-05-27 10:28",
    "2025-05-27 10:41", "2025-05-27 13:05", "2025-05-27 14:32", "2025-05-27 15:44",
    "2025-05-27 19:20", "2025-05-27 21:58", "2025-05-27 22:05", "2025-05-27 23:10",
    "2025-05-28 01:59", "2025-05-28 09:11", "2025-05-28 09:47", "2025-05-28 10:10",
    "2025-05-28 12:17", "2025-05-28 16:53", "2025-05-28 17:07", "2025-05-28 18:40",
    "2025-05-28 19:02", "2025-05-28 20:01", "2025-05-28 20:06", "2025-05-28 20:07",
    "2025-05-28 20:31", "2025-05-28 20:41", "2025-05-28 20:53", "2025-05-28 21:06",
    "2025-05-28 21:20", "2025-05-28 22:33", "2025-05-28 22:39", "2025-05-28 23:29",
    "2025-05-29 00:00", "2025-05-29 00:17", "2025-05-29 01:04", "2025-05-29 01:44",
    "2025-05-29 02:41", "2025-05-29 03:54", "2025-05-29 04:10", "2025-05-29 05:40",
    "2025-05-29 06:29", "2025-05-29 06:46", "2025-05-29 06:51", "2025-05-29 09:17",
    "2025-05-29 10:02", "2025-05-29 10:26", "2025-05-29 10:58", "2025-05-29 11:14",
    "2025-05-29 11:16", "2025-05-29 11:16", "2025-05-29 11:28", "2025-05-29 11:33",
    "2025-05-29 11:44", "2025-05-29 11:48", "2025-05-29 11:50", "2025-05-29 11:58"
]

# Dataset 8 - eighth timestamps (assuming 2025 for Feb-Apr dates)
timestamps8 = [
    "2025-02-15 14:45", "2025-03-11 07:02", "2025-03-12 13:38", "2025-03-12 16:00",
    "2025-03-12 18:34", "2025-03-12 19:58", "2025-03-13 14:54", "2025-03-14 09:38",
    "2025-03-14 18:46", "2025-03-15 10:23", "2025-03-15 11:06", "2025-03-15 11:58",
    "2025-03-15 13:28", "2025-03-15 17:36", "2025-03-16 06:11", "2025-03-16 07:26",
    "2025-03-16 09:24", "2025-03-16 11:11", "2025-03-17 08:40", "2025-03-17 09:26",
    "2025-03-17 09:34", "2025-03-17 09:46", "2025-03-17 10:30", "2025-03-17 12:34",
    "2025-03-17 13:53", "2025-03-17 18:40", "2025-03-17 22:49", "2025-03-17 22:52",
    "2025-03-18 00:41", "2025-03-22 07:22", "2025-03-23 18:21", "2025-03-24 21:55",
    "2025-03-25 14:01", "2025-03-29 12:19", "2025-03-30 00:50", "2025-03-30 13:02",
    "2025-03-30 13:28", "2025-03-31 03:20", "2025-03-31 07:55", "2025-03-31 08:45",
    "2025-03-31 09:49", "2025-03-31 11:27", "2025-03-31 16:09", "2025-03-31 16:34",
    "2025-03-31 18:14", "2025-04-01 07:02", "2025-04-01 07:22", "2025-04-01 10:03",
    "2025-04-01 11:48", "2025-04-01 11:55", "2025-04-01 12:47"
]

# convert to pandas datetime
dates1 = pd.to_datetime(timestamps1)
dates2 = pd.to_datetime(timestamps2)
dates3 = pd.to_datetime(timestamps3)
dates4 = pd.to_datetime(timestamps4)
dates5 = pd.to_datetime(timestamps5)
dates6 = pd.to_datetime(timestamps6)
dates7 = pd.to_datetime(timestamps7)
dates8 = pd.to_datetime(timestamps8)

# Normalization options
def normalize_timeline(dates, method="days"):
    """
    Normalize timeline data relative to the LATEST event (reverse chronological)
    
    Methods:
    - 'days': Days from latest (most recent = t=0, oldest = t=max)
    - 'hours': Hours from latest  
    - 'minutes': Minutes from latest
    - 'normalized': 0-1 scale (latest = 0, oldest = 1)
    """
    latest_time = dates.max()  # Use latest instead of earliest
    
    if method == "days":
        # Reverse: latest events get 0, older events get higher values
        normalized = (latest_time - dates).total_seconds() / (24 * 3600)
        unit = "Days from Latest (t=0)"
    elif method == "hours":
        normalized = (latest_time - dates).total_seconds() / 3600
        unit = "Hours from Latest (t=0)"
    elif method == "minutes":
        normalized = (latest_time - dates).total_seconds() / 60
        unit = "Minutes from Latest (t=0)"
    elif method == "normalized":
        time_diff = (latest_time - dates).total_seconds()
        normalized = time_diff / time_diff.max()
        unit = "Normalized Time (Latest=0, Oldest=1)"
    else:
        raise ValueError("Method must be 'days', 'hours', 'minutes', or 'normalized'")
    
    return normalized, unit

# Function to create frequency data for line plotting
def create_frequency_data(dates, max_days=None):
    days_from_start, _ = normalize_timeline(dates, "days")
    
    if max_days is None:
        max_days = int(days_from_start.max()) + 1
    
    # Create daily frequency counts
    daily_freq = np.zeros(max_days)
    for day in days_from_start:
        day_idx = int(day)
        if day_idx < max_days:
            daily_freq[day_idx] += 1
    
    return np.arange(max_days), daily_freq

# Normalize all eight datasets
days1_from_start, _ = normalize_timeline(dates1, "days")
days2_from_start, _ = normalize_timeline(dates2, "days")
days3_from_start, _ = normalize_timeline(dates3, "days")
days4_from_start, _ = normalize_timeline(dates4, "days")
days5_from_start, _ = normalize_timeline(dates5, "days")
days6_from_start, _ = normalize_timeline(dates6, "days")
days7_from_start, _ = normalize_timeline(dates7, "days")
days8_from_start, _ = normalize_timeline(dates8, "days")

# Find the maximum range for consistent x-axis
max_days = max(int(days1_from_start.max()), int(days2_from_start.max()), 
               int(days3_from_start.max()), int(days4_from_start.max()),
               int(days5_from_start.max()), int(days6_from_start.max()),
               int(days7_from_start.max()), int(days8_from_start.max())) + 1

# Create frequency data for all eight datasets
x1, freq1 = create_frequency_data(dates1, max_days)
x2, freq2 = create_frequency_data(dates2, max_days)
x3, freq3 = create_frequency_data(dates3, max_days)
x4, freq4 = create_frequency_data(dates4, max_days)
x5, freq5 = create_frequency_data(dates5, max_days)
x6, freq6 = create_frequency_data(dates6, max_days)
x7, freq7 = create_frequency_data(dates7, max_days)
x8, freq8 = create_frequency_data(dates8, max_days)

# Create the plot
plt.figure(figsize=(24, 16))
plt.ylim(0, 15)

# Plot all eight datasets as line plots with different styles (more transparent for trend focus)
# plt.plot(x1, freq1, color='steelblue', linewidth=1.5, marker='o', markersize=2, 
#          label='Dataset 1 (Jan-Mar 2025)', alpha=0.4)
# plt.plot(x2, freq2, color='crimson', linewidth=1.5, marker='s', markersize=2, 
#          label='Dataset 2 (Nov 2024-Jan 2025)', alpha=0.4)
# plt.plot(x3, freq3, color='forestgreen', linewidth=1.5, marker='^', markersize=2, 
#          label='Dataset 3 (Dec 2024-May 2025)', alpha=0.4)
# plt.plot(x4, freq4, color='darkorange', linewidth=1.5, marker='d', markersize=2, 
#          label='Dataset 4 (Jan-Mar 2025)', alpha=0.4)
# plt.plot(x5, freq5, color='purple', linewidth=1.5, marker='v', markersize=2, 
#          label='Dataset 5 (Aug-Sep 2024)', alpha=0.4)
# plt.plot(x6, freq6, color='brown', linewidth=1.5, marker='*', markersize=3, 
#          label='Dataset 6 (Dec 2024-Jan 2025)', alpha=0.4)
# plt.plot(x7, freq7, color='hotpink', linewidth=1.5, marker='h', markersize=2, 
#          label='Dataset 7 (Apr-May 2025)', alpha=0.4)
# plt.plot(x8, freq8, color='teal', linewidth=1.5, marker='p', markersize=2, 
#          label='Dataset 8 (Feb-Apr 2025)', alpha=0.4)

# Calculate overall trend by averaging all datasets
combined_freq = np.zeros(max_days)
dataset_count = np.zeros(max_days)

# Add all frequencies and count contributing datasets for each day
for freq in [freq1, freq2, freq3, freq4, freq5, freq6, freq7, freq8]:
    combined_freq += freq
    dataset_count += (freq > 0).astype(int)

# Calculate average frequency (avoiding division by zero)
avg_freq = np.divide(combined_freq, dataset_count, out=np.zeros_like(combined_freq), where=dataset_count!=0)

# Apply Gaussian smoothing for trend line
smoothed_trend = gaussian_filter1d(avg_freq, sigma=2.0)

# Plot the smoothed overall trend
x_trend = np.arange(max_days)
plt.plot(x_trend, smoothed_trend, color='black', linewidth=4, alpha=0.8, 
         label='Overall Trend (Smoothed)', linestyle='-', zorder=10)


# Formatting
plt.xlabel('Days from Latest Event (t=0 = Most Recent)', fontsize=15)
plt.ylabel('Frequency (Number of Events)', fontsize=15)
plt.title('Event Frequency Comparison - Eight Datasets (Latest → Oldest)', fontsize=20, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend(fontsize=9, loc='upper right')


# Set x-axis to start from 0 and cut at 30 days for better scale
plt.xlim(0,60)
# Y-axis limit is already set to 30 after figure creation

# Add statistics for all eight datasets
stats_text = f'Dataset 1: {len(dates1)} events over {int(days1_from_start.max())+1} days\n'
stats_text += f'Dataset 2: {len(dates2)} events over {int(days2_from_start.max())+1} days\n'
stats_text += f'Dataset 3: {len(dates3)} events over {int(days3_from_start.max())+1} days\n'
stats_text += f'Dataset 4: {len(dates4)} events over {int(days4_from_start.max())+1} days\n'
stats_text += f'Dataset 5: {len(dates5)} events over {int(days5_from_start.max())+1} days\n'
stats_text += f'Dataset 6: {len(dates6)} events over {int(days6_from_start.max())+1} days\n'
stats_text += f'Dataset 7: {len(dates7)} events over {int(days7_from_start.max())+1} days\n'
stats_text += f'Dataset 8: {len(dates8)} events over {int(days8_from_start.max())+1} days'

plt.text(0.02, 0.98, stats_text, 
         transform=plt.gca().transAxes, verticalalignment='top',
         bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9))

plt.tight_layout()
plt.show()

# Print summary statistics for all eight datasets
print("Timeline Analysis:")
print("\nDataset 1:")
print(f"First event: {dates1.min()}")
print(f"Last event: {dates1.max()}")
print(f"Total duration: {(dates1.max() - dates1.min()).days} days")
print(f"Number of events: {len(dates1)}")

print("\nDataset 2:")
print(f"First event: {dates2.min()}")
print(f"Last event: {dates2.max()}")
print(f"Total duration: {(dates2.max() - dates2.min()).days} days")
print(f"Number of events: {len(dates2)}")

print("\nDataset 3:")
print(f"First event: {dates3.min()}")
print(f"Last event: {dates3.max()}")
print(f"Total duration: {(dates3.max() - dates3.min()).days} days")
print(f"Number of events: {len(dates3)}")

print("\nDataset 4:")
print(f"First event: {dates4.min()}")
print(f"Last event: {dates4.max()}")
print(f"Total duration: {(dates4.max() - dates4.min()).days} days")
print(f"Number of events: {len(dates4)}")

print("\nDataset 5:")
print(f"First event: {dates5.min()}")
print(f"Last event: {dates5.max()}")
print(f"Total duration: {(dates5.max() - dates5.min()).days} days")
print(f"Number of events: {len(dates5)}")

print("\nDataset 6:")
print(f"First event: {dates6.min()}")
print(f"Last event: {dates6.max()}")
print(f"Total duration: {(dates6.max() - dates6.min()).days} days")
print(f"Number of events: {len(dates6)}")

print("\nDataset 7:")
print(f"First event: {dates7.min()}")
print(f"Last event: {dates7.max()}")
print(f"Total duration: {(dates7.max() - dates7.min()).days} days")
print(f"Number of events: {len(dates7)}")

print("\nDataset 8:")
print(f"First event: {dates8.min()}")
print(f"Last event: {dates8.max()}")
print(f"Total duration: {(dates8.max() - dates8.min()).days} days")
print(f"Number of events: {len(dates8)}")

# Show event density by day for all datasets
daily_counts1 = pd.Series(dates1.date).value_counts().sort_index()
daily_counts2 = pd.Series(dates2.date).value_counts().sort_index()
daily_counts3 = pd.Series(dates3.date).value_counts().sort_index()
daily_counts4 = pd.Series(dates4.date).value_counts().sort_index()
daily_counts5 = pd.Series(dates5.date).value_counts().sort_index()
daily_counts6 = pd.Series(dates6.date).value_counts().sort_index()
daily_counts7 = pd.Series(dates7.date).value_counts().sort_index()
daily_counts8 = pd.Series(dates8.date).value_counts().sort_index()

print(f"\nDataset 1 - Event density:")
print(f"Most active day: {daily_counts1.idxmax()} ({daily_counts1.max()} events)")
print(f"Average events per active day: {daily_counts1.mean():.1f}")

print(f"\nDataset 2 - Event density:")
print(f"Most active day: {daily_counts2.idxmax()} ({daily_counts2.max()} events)")
print(f"Average events per active day: {daily_counts2.mean():.1f}")

print(f"\nDataset 3 - Event density:")
print(f"Most active day: {daily_counts3.idxmax()} ({daily_counts3.max()} events)")
print(f"Average events per active day: {daily_counts3.mean():.1f}")

print(f"\nDataset 4 - Event density:")
print(f"Most active day: {daily_counts4.idxmax()} ({daily_counts4.max()} events)")
print(f"Average events per active day: {daily_counts4.mean():.1f}")

print(f"\nDataset 5 - Event density:")
print(f"Most active day: {daily_counts5.idxmax()} ({daily_counts5.max()} events)")
print(f"Average events per active day: {daily_counts5.mean():.1f}")

print(f"\nDataset 6 - Event density:")
print(f"Most active day: {daily_counts6.idxmax()} ({daily_counts6.max()} events)")
print(f"Average events per active day: {daily_counts6.mean():.1f}")

print(f"\nDataset 7 - Event density:")
print(f"Most active day: {daily_counts7.idxmax()} ({daily_counts7.max()} events)")
print(f"Average events per active day: {daily_counts7.mean():.1f}")

print(f"\nDataset 8 - Event density:")
print(f"Most active day: {daily_counts8.idxmax()} ({daily_counts8.max()} events)")
print(f"Average events per active day: {daily_counts8.mean():.1f}")

# Generate workload file from smoothed trend data
print("\n" + "="*50)
print("GENERATING WORKLOAD FILE")
print("="*50)

# Take first 60 days of smoothed trend (60 seconds in workload)
workload_duration = 60
workload_data = []

for day in range(min(workload_duration, len(smoothed_trend))):
    duration = 1  # Each day = 1 second
    rps = max(1, int(round(smoothed_trend[day])))  # Convert to integer RPS, minimum 1
    workload_data.append((duration, rps))
    
# Write to CSV file
import csv
workload_filename = "smoothed_workload.csv"

with open(workload_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['duration', 'rps'])  # Header
    for duration, rps in workload_data:
        writer.writerow([duration, rps])

print(f"Workload file generated: {workload_filename}")
print(f"Total duration: {len(workload_data)} seconds")
print(f"RPS range: {min([rps for _, rps in workload_data])} - {max([rps for _, rps in workload_data])}")

# Print first 10 rows as preview
print("\nPreview (first 10 rows):")
print("duration,rps")
for i, (duration, rps) in enumerate(workload_data[:10]):
    print(f"{duration},{rps}")
if len(workload_data) > 10:
    print("...")


print(f"\nOverall trend:")
# print(f"Most active day: {smoothed_trend.idxmax()} ({smoothed_trend.max()} events)")
# print(f"Average events per active day: {smoothed_trend.mean():.1f}")
# print(smoothed_trend)
for i in range(len(smoothed_trend)):
    print(f"{i}: {int(smoothed_trend[i])}")