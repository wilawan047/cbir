-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3307
-- Generation Time: Sep 02, 2025 at 11:35 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `projectdb`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `status` enum('active','inactive') NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `role` varchar(20) NOT NULL DEFAULT 'admin'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `username`, `password`, `email`, `first_name`, `last_name`, `status`, `created_at`, `role`) VALUES
(2, 'admin', 'pbkdf2:sha256:100000', 'admin@example.com', 'Admin', 'User2', 'inactive', '2025-04-05 08:59:04', 'admin'),
(3, 'enny1', 'scrypt:32768:8:1$ezZG8MVHsj7D20Bm$5562e0a4786aa155ac8df9892dcba8e7e788a2e47f9c56f4de6fe7ef75f0009d3a6c4766c9b1263c96a0ced16deb69d86b54c42df5882f119b3c1ad3c6f89ff2', 'enianjola@gmail.com', 'enny', 'Sena', 'active', '2025-04-05 10:54:54', 'admin'),
(4, 'mike', 'scrypt:32768:8:1$DFupAB3T9Um7lewm$dc99d456001393507fa7b4d15e2235747fd3ebbcebb5bc4924852086674090a209d17a7ee77b0792832297a7cf43c7a9efd74a12b42e96f9a706eeb831c30afb', 'st25364@bru.ac.th', 'oladele', 'senbanjo', 'active', '2025-05-22 10:21:07', 'superadmin'),
(6, 'faii', 'scrypt:32768:8:1$0jMnosWKMZMA7jQ3$2b6b3b72af5f18b8fc7cef48f592d4c1393cf119d8bcd45a10e794647c8ab93caa4b532fd3169f30b76d6ac0e94f48fa769dfc6e3f911aeef454a3178eb63530', 'baanthai.buriram@gmail.com', 'faidat', 'OJO', 'inactive', '2025-08-11 12:04:58', 'admin'),
(7, 'testadmin', 'scrypt:32768:8:1$WJttknxt8PPDnxkl$cb3cefb65397e625b6c7c9a07b8a5e0ad7e9189361f4d64ca48e6012b22cd3c33c7e75eee1f0c81a0d63194ada445f47fbda9d8faca152f92957ffcfc8358cae', 'test@example.com', 'Test1', 'Admin', 'active', '2025-08-14 10:59:11', 'admin');

-- --------------------------------------------------------

--
-- Table structure for table `house`
--

CREATE TABLE `house` (
  `h_id` int(11) NOT NULL,
  `p_id` int(11) NOT NULL,
  `t_id` int(11) DEFAULT NULL,
  `h_title` varchar(255) NOT NULL,
  `h_description` text DEFAULT NULL,
  `price` decimal(12,2) DEFAULT NULL,
  `bedrooms` int(11) DEFAULT NULL,
  `bathrooms` int(11) DEFAULT NULL,
  `living_area` decimal(10,2) DEFAULT NULL,
  `parking_space` int(11) DEFAULT NULL,
  `no_of_floors` int(11) DEFAULT NULL,
  `a_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `status` varchar(50) DEFAULT 'Available',
  `latitude` decimal(10,7) DEFAULT NULL,
  `longitude` decimal(10,7) DEFAULT NULL,
  `f_id` int(11) DEFAULT NULL,
  `view_count` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `house`
--

INSERT INTO `house` (`h_id`, `p_id`, `t_id`, `h_title`, `h_description`, `price`, `bedrooms`, `bathrooms`, `living_area`, `parking_space`, `no_of_floors`, `a_id`, `created_at`, `updated_at`, `status`, `latitude`, `longitude`, `f_id`, `view_count`) VALUES
(12, 2, 5, 'BAANTHAI BURIRAM 5 SIZE M', 'โครงการบ้านไท บ้านเดี่ยวชั้นเดียว แบบบ้านสไตล์โมเดิร์น\r\nเหมาะกับคนรุ่นใหม่ วัยทำงาน ต้องการความเงียบสงบกับราคาบ้านที่เอื้อมถึง\r\nพร้อมสิ่งอำนวย เพราะอยู่ในโซนเทศบาลตำบลอิสาณ\r\nใกล้ร้านสะดวกซื้อมากมาย CJ Mall , 7-11\r\nใกล้ห้างสรรพสินค้าชั้นนำ โรบินสัน บิ๊กซี แม็กโคร ทวีกิจซุเปอร์เซ็นเตอร์', 1800000.00, 3, 2, 100.00, 1, 2, NULL, '2025-08-18 11:37:01', '2025-08-22 12:17:25', 'available', 14.9982500, 103.0700600, 4, 5),
(13, 2, 5, 'BAANTHAI BURIRAM 5 SIZE L', 'โครงการบ้านไท บ้านเดี่ยวชั้นเดียว แบบบ้านสไตล์โมเดิร์น\r\nเหมาะกับคนรุ่นใหม่ วัยทำงาน ต้องการความเงียบสงบกับราคาบ้านที่เอื้อมถึง\r\nพร้อมสิ่งอำนวย เพราะอยู่ในโซนเทศบาลตำบลอิสาณ\r\nใกล้ร้านสะดวกซื้อมากมาย CJ Mall , 7-11\r\nใกล้ห้างสรรพสินค้าชั้นนำ โรบินสัน บิ๊กซี แม็กโคร ทวีกิจซุเปอร์เซ็นเตอร์', 1950000.00, 3, 2, 120.00, 2, 1, NULL, '2025-08-18 12:20:21', '2025-09-02 07:23:44', 'available', 14.9982500, 103.0700600, 4, 3),
(14, 2, 5, 'BAANTHAI BURIRAM 5 SIZE S', 'โครงการบ้านไท บ้านเดี่ยวชั้นเดียว แบบบ้านสไตล์โมเดิร์น\r\nเหมาะกับคนรุ่นใหม่ วัยทำงาน ต้องการความเงียบสงบกับราคาบ้านที่เอื้อมถึง\r\nพร้อมสิ่งอำนวย เพราะอยู่ในโซนเทศบาลตำบลอิสาณ\r\nใกล้ร้านสะดวกซื้อมากมาย CJ Mall , 7-11\r\nใกล้ห้างสรรพสินค้าชั้นนำ โรบินสัน บิ๊กซี แม็กโคร ทวีกิจซุเปอร์เซ็นเตอร์', 1000000.00, 2, 1, 80.00, 1, 1, NULL, '2025-08-18 14:18:57', '2025-08-25 06:12:50', 'available', 14.9982500, 103.0700600, NULL, 1),
(15, 2, 5, 'BAANTHAI BURIRAM TYPE A', 'โครงการบ้านไท 4 แยกกระสัง โซนโรบินสันบ้านบัว\r\nพิกัด: สี่แยกกระสัง ตรงข้ามโกลบอลเฮ้าส์\r\n3 ห้องนอน 2 ห้องน้ำ 1 ห้องครัว ที่จอดรถ 1 คัน\r\nพร้อมพื้นที่รอบบ้าน\r\nจองทำเล รับไปเลย Promotions ส่งท้ายปี\r\nส่วนลดจสูงสุด 200,000 บาท\r\nของแถมเลือกได้ มีหลายรายการ\r\nที่นี่ที่เดียว บ้านสวยราคาไม่ถึง 2 ล้าน\r\nเช็คเครดิตก่อน ยื่นฟรี ไม่มีค่าใช้จ่าย\r\nรู้ก่อน วางแผนก่อน เตรียมตัวได้เร็ว\r\nกู้ได้ทุกอาชีพดันให้ทุกเคส ช่วยวางแผนทุกขั้นตอน ติดตามผลการยื่นกู้ให้ฟรี\r\n', 1690000.00, 3, 2, 100.00, 1, 1, NULL, '2025-08-19 08:26:24', '2025-09-01 06:08:21', 'available', 14.9982500, 103.0700600, 4, 3),
(16, 2, 1, 'BAANTHAI BURIRAM TYPE B', 'โครงการบ้านไท 4 แยกกระสัง โซนโรบินสันบ้านบัว\r\nพิกัด: สี่แยกกระสัง ตรงข้ามโกลบอลเฮ้าส์\r\n3 ห้องนอน 2 ห้องน้ำ 1 ห้องครัว ที่จอดรถ 1 คัน\r\nพร้อมพื้นที่รอบบ้าน\r\nจองทำเล รับไปเลย Promotions ส่งท้ายปี\r\nส่วนลดจสูงสุด 200,000 บาท\r\nของแถมเลือกได้ มีหลายรายการ\r\nที่นี่ที่เดียว บ้านสวยราคาไม่ถึง 2 ล้าน\r\nเช็คเครดิตก่อน ยื่นฟรี ไม่มีค่าใช้จ่าย\r\nรู้ก่อน วางแผนก่อน เตรียมตัวได้เร็ว\r\nกู้ได้ทุกอาชีพดันให้ทุกเคส ช่วยวางแผนทุกขั้นตอน ติดตามผลการยื่นกู้ให้ฟรี', 1990000.00, 3, 2, 100.00, 2, 2, NULL, '2025-08-19 08:48:07', '2025-09-01 06:03:31', 'available', 14.9982500, 103.0700600, 4, 4),
(17, 6, 5, 'CASA MALIWAN บ้านชั้นเดี่ยว', 'คาซ่า มะลิวัลย์ เป็นโครงการบ้านเดี่ยวที่ออกแบบอย่างเรียบหรู สไตล์โมเดิร์น โอบล้อมด้วยบรรยากาศสงบและเป็นส่วนตัว เหมาะสำหรับครอบครัวที่ต้องการบ้านคุณภาพในราคาที่เข้าถึงได้\r\nบ้านเดี่ยวชั้นเดียว: 3 ห้องนอน 2 ห้องน้ำ ที่จอดรถ 1 คัน\r\nบ้านเดี่ยวสองชั้น: 3 ห้องนอน 2 ห้องน้ำ ที่จอดรถ 2 คัน\r\nจำนวนยูนิตรวม: 36 หลัง\r\nราคาเริ่มต้นเพียง 1.79 ล้านบาท\r\n\r\nสิ่งอำนวยความสะดวกภายในโครงการ\r\nสวนหย่อมส่วนกลาง\r\nระบบรักษาความปลอดภัย 24 ชั่วโมง พร้อมกล้อง CCTV\r\n\r\nทำเลที่ตั้ง\r\nโครงการตั้งอยู่ใกล้สิ่งอำนวยความสะดวกในเมือง ไม่ว่าจะเป็นห้างสรรพสินค้า โรงเรียน มหาวิทยาลัย และโรงพยาบาล เดินทางสะดวกด้วยถนนมะลิวัลย์\r\nคาซ่า มะลิวัลย์ ขอนแก่น — บ้านที่ลงตัวทั้งดีไซน์ ราคา และคุณภาพชีวิต', 1790000.00, 3, 2, 100.00, 1, 1, NULL, '2025-08-19 09:13:58', '2025-08-19 09:19:12', 'available', 16.2810100, 102.4343200, 4, 0),
(18, 6, 1, 'CASA MALIWAN SIZE M', 'คาซ่า มะลิวัลย์ เป็นโครงการบ้านเดี่ยวที่ออกแบบอย่างเรียบหรู สไตล์โมเดิร์น โอบล้อมด้วยบรรยากาศสงบและเป็นส่วนตัว เหมาะสำหรับครอบครัวที่ต้องการบ้าน\r\n\r\nคุณภาพในราคาที่เข้าถึงได้\r\nบ้านเดี่ยวชั้นเดียว: 3 ห้องนอน 2 ห้องน้ำ ที่จอดรถ 1 คัน\r\nบ้านเดี่ยวสองชั้น: 3 ห้องนอน 2 ห้องน้ำ ที่จอดรถ 2 คัน\r\nจำนวนยูนิตรวม: 36 หลัง\r\nราคาเริ่มต้นเพียง 1.79 ล้านบาท\r\n\r\nสิ่งอำนวยความสะดวกภายในโครงการ\r\nสวนหย่อมส่วนกลาง\r\nระบบรักษาความปลอดภัย 24 ชั่วโมง พร้อมกล้อง CCTV\r\n\r\nทำเลที่ตั้ง\r\nโครงการตั้งอยู่ใกล้สิ่งอำนวยความสะดวกในเมือง ไม่ว่าจะเป็นห้างสรรพสินค้า โรงเรียน มหาวิทยาลัย และโรงพยาบาล เดินทางสะดวกด้วยถนนมะลิวัลย์\r\n\r\nคาซ่า มะลิวัลย์ ขอนแก่น — บ้านที่ลงตัวทั้งดีไซน์ ราคา และคุณภาพชีวิต', 2590000.00, 3, 2, 100.00, 2, 2, NULL, '2025-08-19 09:26:39', '2025-08-25 06:12:42', 'available', 16.2810100, 102.4343200, 4, 2),
(19, 6, 1, 'CASA MALIWAN SIZE L', 'คาซ่า มะลิวัลย์ เป็นโครงการบ้านเดี่ยวที่ออกแบบอย่างเรียบหรู สไตล์โมเดิร์น โอบล้อมด้วยบรรยากาศสงบและเป็นส่วนตัว เหมาะสำหรับครอบครัวที่ต้องการบ้าน\r\n\r\nคุณภาพในราคาที่เข้าถึงได้\r\nบ้านเดี่ยวชั้นเดียว: 3 ห้องนอน 2 ห้องน้ำ ที่จอดรถ 1 คัน\r\nบ้านเดี่ยวสองชั้น: 3 ห้องนอน 2 ห้องน้ำ ที่จอดรถ 2 คัน\r\nจำนวนยูนิตรวม: 36 หลัง\r\nราคาเริ่มต้นเพียง 1.79 ล้านบาท\r\n\r\nสิ่งอำนวยความสะดวกภายในโครงการ\r\nสวนหย่อมส่วนกลาง\r\nระบบรักษาความปลอดภัย 24 ชั่วโมง พร้อมกล้อง CCTV\r\n\r\nทำเลที่ตั้ง\r\nโครงการตั้งอยู่ใกล้สิ่งอำนวยความสะดวกในเมือง ไม่ว่าจะเป็นห้างสรรพสินค้า โรงเรียน มหาวิทยาลัย และโรงพยาบาล เดินทางสะดวกด้วยถนนมะลิวัลย์\r\n\r\nคาซ่า มะลิวัลย์ ขอนแก่น — บ้านที่ลงตัวทั้งดีไซน์ ราคา และคุณภาพชีวิต', 2990000.00, 4, 3, 100.00, 3, 2, NULL, '2025-08-19 09:41:27', '2025-08-28 05:39:32', 'available', 16.2810100, 102.4343200, 3, 5),
(20, 3, 5, 'LAVILLA KALASIN ชั้นเดี่ยว', 'ลา วิลล่า กาฬสินธุ์ (La Villa Kalasin)\r\nลา วิลล่า กาฬสินธุ์ เป็นโครงการบ้านเดี่ยวดีไซน์ทันสมัย ฟังก์ชันครบ ตอบโจทย์ทั้งครอบครัวขนาดเล็กและใหญ่ ตั้งอยู่บนทำเลศักยภาพใกล้ใจกลางเมืองกาฬสินธุ์ เดินทางสะดวกและรายล้อมด้วยสิ่งอำนวยความสะดวกครบครัน\r\n\r\nบ้านเดี่ยวชั้นเดียว: 3 ห้องนอน 2 ห้องน้ำ พื้นที่ใช้สอยประมาณ 120 ตร.ม.\r\nบ้านเดี่ยวสองชั้น: 4 ห้องนอน 2 ห้องน้ำ\r\nจำนวนยูนิตรวม: 34 หลัง บนพื้นที่โครงการประมาณ 5 ไร่ 2 งาน 88 ตร.ว.\r\nราคาเริ่มต้นเพียง 1.55 ล้านบาท (บ้านชั้นเดียว) และ 2.19 ล้านบาท (บ้านสองชั้น)\r\n\r\nสิ่งอำนวยความสะดวกภายในโครงการ\r\nสวนสาธารณะสำหรับพักผ่อน\r\nระบบรักษาความปลอดภัยตลอด 24 ชั่วโมง พร้อมเจ้าหน้าที่\r\n\r\nทำเลที่ตั้ง\r\nโครงการตั้งอยู่ใกล้ใจกลางเมืองกาฬสินธุ์ ใกล้โรงพยาบาลกาฬสินธุ์, บิ๊กซี, เทสโก้โลตัส และสถานที่สำคัญอื่น ๆ เดินทางสะดวกสบาย', 1550000.00, 3, 2, 120.00, 1, 1, NULL, '2025-08-19 09:52:57', '2025-08-27 08:25:04', 'available', 16.2510000, 103.3240100, 4, 9),
(21, 3, 1, 'LA VILLA KALASIN สองชั้น', 'ลา วิลล่า กาฬสินธุ์ เป็นโครงการบ้านเดี่ยวดีไซน์ทันสมัย ฟังก์ชันครบ ตอบโจทย์ทั้งครอบครัวขนาดเล็กและใหญ่ ตั้งอยู่บนทำเลศักยภาพใกล้ใจกลางเมืองกาฬสินธุ์ เดินทางสะดวกและรายล้อมด้วยสิ่งอำนวยความสะดวกครบครัน\r\n\r\nบ้านเดี่ยวชั้นเดียว: 3 ห้องนอน 2 ห้องน้ำ พื้นที่ใช้สอยประมาณ 120 ตร.ม.\r\nบ้านเดี่ยวสองชั้น: 4 ห้องนอน 2 ห้องน้ำ\r\nจำนวนยูนิตรวม: 34 หลัง บนพื้นที่โครงการประมาณ 5 ไร่ 2 งาน 88 ตร.ว.\r\nราคาเริ่มต้นเพียง 1.55 ล้านบาท (บ้านชั้นเดียว) และ 2.19 ล้านบาท (บ้านสองชั้น)\r\n\r\nสิ่งอำนวยความสะดวกภายในโครงการ\r\nสวนสาธารณะสำหรับพักผ่อน\r\nระบบรักษาความปลอดภัยตลอด 24 ชั่วโมง พร้อมเจ้าหน้าที่\r\n\r\nทำเลที่ตั้ง\r\nโครงการตั้งอยู่ใกล้ใจกลางเมืองกาฬสินธุ์ ใกล้โรงพยาบาลกาฬสินธุ์, บิ๊กซี, เทสโก้โลตัส และสถานที่สำคัญอื่น ๆ เดินทางสะดวกสบาย', 2190000.00, 4, 2, 100.00, 2, 2, NULL, '2025-08-19 10:00:11', '2025-09-01 06:35:19', 'available', 0.0000000, 0.0000000, 3, 8),
(22, 6, 1, 'LAVILLA NONGLOUP', 'ลาวิลล่าหนองหลุบ LA VILLA\r\nโครงการใหม่ บ้านเดี่ยว 2 ชั้นเมืองขอนแก่น ใกล้สนามบิน\r\nเดินทางสะดวก บ้านน่าอยู่\r\nพื้นที่กว้างขวาง อากาศดี๊ดี\r\nผ่อนสบายๆ ราคาที่คุณเอื้อมถึงจ้า\r\n3 ห้องนอน\r\n3 ห้องน้ำ\r\nที่จอดรถ 2 คัน\r\nพื้นที่ 50 ตรว.', 3090000.00, 3, 3, 153.00, 2, 2, NULL, '2025-08-19 11:17:51', '2025-09-02 07:21:43', 'available', 16.2751300, 102.4537400, 4, 21);

-- --------------------------------------------------------

--
-- Table structure for table `house_features`
--

CREATE TABLE `house_features` (
  `f_id` int(11) NOT NULL,
  `f_name` varchar(100) NOT NULL,
  `f_description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `f_image` varchar(255) DEFAULT NULL,
  `a_id` int(11) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `house_features`
--

INSERT INTO `house_features` (`f_id`, `f_name`, `f_description`, `created_at`, `f_image`, `a_id`, `updated_at`) VALUES
(3, '4 ห้องนอน', 'Beautifully landscaped garden area.', '2025-05-26 08:42:59', 'pexels-pixabay-271624.jpg', 4, '2025-07-01 09:50:13'),
(4, '3 ห้องนอน', 'บ้านสวยมากก', '2025-05-27 04:12:50', 'pexels-jvdm-1454806.jpg', 4, '2025-07-22 09:54:43'),
(8, '2 ห้องนอน', 'yess', '2025-08-19 09:33:44', '4.jpg', 4, '2025-08-21 11:14:24');

-- --------------------------------------------------------

--
-- Table structure for table `house_images`
--

CREATE TABLE `house_images` (
  `id` int(11) NOT NULL,
  `house_id` int(11) NOT NULL,
  `image_url` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `is_main` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `house_images`
--

INSERT INTO `house_images` (`id`, `house_id`, `image_url`, `created_at`, `is_main`) VALUES
(19, 12, 'uploads/baan_1_1755517021.png', '2025-08-18 11:37:01', 1),
(20, 12, 'uploads/1755518128_baan_2.png', '2025-08-18 11:55:28', 0),
(21, 12, 'uploads/1755518128_site_plan.png', '2025-08-18 11:55:28', 0),
(22, 13, 'uploads/baan_1_l_1755519621.png', '2025-08-18 12:20:21', 1),
(23, 13, 'uploads/baan_2_l_1755519621.png', '2025-08-18 12:20:21', 0),
(24, 13, 'uploads/inside_1_1755519621.png', '2025-08-18 12:20:21', 0),
(25, 13, 'uploads/inside_2_1755519621.png', '2025-08-18 12:20:21', 0),
(26, 13, 'uploads/1755519688_site_plan.png', '2025-08-18 12:21:28', 0),
(27, 14, 'uploads/baan_s_1_1755526737.png', '2025-08-18 14:18:57', 1),
(28, 14, 'uploads/baan_s_2_1755526737.png', '2025-08-18 14:18:57', 0),
(29, 14, 'uploads/inside_s1_1755526737.png', '2025-08-18 14:18:57', 0),
(30, 14, 'uploads/inside_s2_1755526737.png', '2025-08-18 14:18:57', 0),
(31, 14, 'uploads/inside_s3_1755526737.png', '2025-08-18 14:18:57', 0),
(32, 14, 'uploads/site_plan_1755526737.png', '2025-08-18 14:18:57', 0),
(37, 15, 'uploads/baan_4s_type_a_2_1755591984.png', '2025-08-19 08:26:24', 1),
(39, 15, 'uploads/1755592530_453725804_950206476909187_3039174782847369027_n.png', '2025-08-19 08:35:30', 0),
(40, 15, 'uploads/1755592530_475383873_1069696478293519_9211460356204302597_n.png', '2025-08-19 08:35:30', 0),
(41, 15, 'uploads/1755592530_AJtDgRGFrv.png', '2025-08-19 08:35:30', 0),
(42, 15, 'uploads/1755592530_baan_4s_type_a_2.png', '2025-08-19 08:35:30', 0),
(43, 15, 'uploads/1755592530_image.png', '2025-08-19 08:35:30', 0),
(44, 16, 'uploads/27499_1_1755593287.png', '2025-08-19 08:48:07', 1),
(45, 16, 'uploads/27500_1_1755593287.png', '2025-08-19 08:48:07', 0),
(46, 16, 'uploads/27501_1_1755593287.png', '2025-08-19 08:48:07', 0),
(47, 16, 'uploads/27503_1_1755593287.png', '2025-08-19 08:48:07', 0),
(49, 16, 'uploads/1755593318_65857241_902151243453171_2866983385539018752_n.png', '2025-08-19 08:48:38', 0),
(50, 16, 'uploads/1755593318_image_1.png', '2025-08-19 08:48:38', 0),
(51, 16, 'uploads/1755593318_image_2.png', '2025-08-19 08:48:38', 0),
(53, 17, 'uploads/637569091994375841-House1_cover2_1755594838.png', '2025-08-19 09:13:58', 0),
(54, 17, 'uploads/637569092158834293-House1_plan_1755594838.png', '2025-08-19 09:13:58', 0),
(55, 17, 'uploads/LINE_ALBUM___2_1755594838.png', '2025-08-19 09:13:58', 1),
(59, 18, 'uploads/ca196e2b8adceb2c0049beb686db27d2_1755595599.png', '2025-08-19 09:26:39', 1),
(60, 18, 'uploads/1755595732_2e206a2dfc5e8f6c3798204f23d3ece5.png', '2025-08-19 09:28:52', 0),
(61, 18, 'uploads/1755595732_6543f25a293413f0e882bc774c091a73.png', '2025-08-19 09:28:52', 0),
(64, 19, 'uploads/sm23hpc5ytoy5bvrc7wbez1em67ywfjnwkchycdnax0zle1wujl6lacnmsyynytw39nrwmvw213q50czm00zb0jb2ov9pj98j7r6x8v42qix8y2tk6lq3cbdxcbdm4ow.jpg_1755596487.png', '2025-08-19 09:41:27', 1),
(65, 19, 'uploads/1755596546_637569094995476388-CS_MLW_HouseB_cover.jpg.png', '2025-08-19 09:42:26', 0),
(66, 19, 'uploads/1755596546_637569095297626576-CS_MLW_HouseB_img.png', '2025-08-19 09:42:26', 0),
(68, 20, 'uploads/LINE_ALBUM___2_1755597177.png', '2025-08-19 09:52:57', 1),
(69, 20, 'uploads/1755597292_637569092158834293-House1_plan.png', '2025-08-19 09:54:52', 0),
(70, 21, 'uploads/100051498_163247088548284_6174265717089632256_n.jpg_1755597611.png', '2025-08-19 10:00:11', 1),
(71, 21, 'uploads/1755597642_image_1.png', '2025-08-19 10:00:42', 0),
(72, 21, 'uploads/1755597642_image_2.png', '2025-08-19 10:00:42', 0),
(73, 22, 'uploads/v6FEQR4Ihf5bzbiiLYvlPKdcOwnxSYb3uENlOPb2_1755602271.jpg', '2025-08-19 11:17:51', 1),
(84, 22, 'uploads/1755602325_LINE_ALBUM____12_2.png', '2025-08-19 11:18:45', 0),
(85, 22, 'uploads/1755602435_LINE_ALBUM____7_1.png', '2025-08-19 11:20:35', 0),
(86, 22, 'uploads/1755602451_LINE_ALBUM____3_1.png', '2025-08-19 11:20:51', 0),
(87, 22, 'uploads/1755602451_LINE_ALBUM____6_2.png', '2025-08-19 11:20:51', 0),
(88, 22, 'uploads/1755602469_0a0430c98224718512f072b32c752840.png', '2025-08-19 11:21:09', 0),
(89, 22, 'uploads/1755602469_eyJidWNrZXQiOiJuYXlvby1wcm9kdWN0aW9uIiwia2V5IjoiYXR0YWNobWVudHMvcG9zdHMvMzAyOTAvZ2FsbGVyeS83NGZjMTRjZTA2N2JiNmE4ZWJmYWFjZGM1NGU4NDc3ZC5qcGVnIiwiZWRpdHMiOnsicmVzaXplIjp7IndpZHRoIjoxM.png', '2025-08-19 11:21:09', 0),
(90, 22, 'uploads/1755602479_1080x1080-03-1.png', '2025-08-19 11:21:19', 0),
(91, 22, 'uploads/1755602479_1920x1080.png', '2025-08-19 11:21:19', 0);

-- --------------------------------------------------------

--
-- Table structure for table `house_type`
--

CREATE TABLE `house_type` (
  `t_id` int(11) NOT NULL,
  `t_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `a_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `t_image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `house_type`
--

INSERT INTO `house_type` (`t_id`, `t_name`, `description`, `a_id`, `created_at`, `updated_at`, `t_image`) VALUES
(1, 'บ้านสองชั้น', 'A stand-alone house not attached to any other house.', 1, '2025-05-22 08:59:04', '2025-08-21 13:43:28', '3jqkFhc82HKiL2NfFmY5M5TnlMFWbSb5YqQlxOvj.jpg'),
(5, 'บ้านชั้นเดียว', 'สวยจริงงง', NULL, '2025-05-28 04:16:30', '2025-08-28 05:35:36', 'baan_1.png');

-- --------------------------------------------------------

--
-- Table structure for table `house_views`
--

CREATE TABLE `house_views` (
  `id` int(11) NOT NULL,
  `house_id` int(11) NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `house_views`
--

INSERT INTO `house_views` (`id`, `house_id`, `ip_address`, `created_at`) VALUES
(2, 21, '127.0.0.1', '2025-08-22 11:12:22'),
(3, 21, '127.0.0.1', '2025-08-22 11:13:39'),
(4, 21, '127.0.0.1', '2025-08-22 11:15:22'),
(5, 21, '127.0.0.1', '2025-08-22 11:15:32'),
(6, 12, '127.0.0.1', '2025-08-22 11:15:41'),
(9, 21, '127.0.0.1', '2025-08-22 11:17:43'),
(10, 12, '127.0.0.1', '2025-08-22 11:20:15'),
(11, 19, '127.0.0.1', '2025-08-22 11:39:09'),
(12, 12, '127.0.0.1', '2025-08-22 12:10:13'),
(13, 12, '127.0.0.1', '2025-08-22 12:17:23'),
(14, 12, '127.0.0.1', '2025-08-22 12:17:25'),
(15, 22, '127.0.0.1', '2025-08-22 14:05:18'),
(16, 18, '127.0.0.1', '2025-08-22 16:43:55'),
(17, 16, '127.0.0.1', '2025-08-22 16:44:04'),
(18, 13, '127.0.0.1', '2025-08-23 02:03:48'),
(19, 19, '127.0.0.1', '2025-08-23 02:04:25'),
(20, 22, '127.0.0.1', '2025-08-23 06:27:31'),
(21, 22, '127.0.0.1', '2025-08-23 06:37:06'),
(22, 22, '127.0.0.1', '2025-08-23 06:49:59'),
(23, 22, '127.0.0.1', '2025-08-23 06:50:14'),
(24, 22, '127.0.0.1', '2025-08-23 07:13:31'),
(25, 22, '127.0.0.1', '2025-08-25 06:12:17'),
(26, 16, '127.0.0.1', '2025-08-25 06:12:34'),
(27, 18, '127.0.0.1', '2025-08-25 06:12:42'),
(28, 14, '127.0.0.1', '2025-08-25 06:12:50'),
(29, 15, '127.0.0.1', '2025-08-26 12:28:32'),
(30, 19, '127.0.0.1', '2025-08-26 12:57:16'),
(31, 22, '127.0.0.1', '2025-08-27 07:10:09'),
(32, 22, '127.0.0.1', '2025-08-27 07:17:36'),
(33, 20, '127.0.0.1', '2025-08-27 07:18:18'),
(34, 20, '127.0.0.1', '2025-08-27 07:22:41'),
(35, 20, '127.0.0.1', '2025-08-27 07:23:30'),
(36, 22, '127.0.0.1', '2025-08-27 07:24:23'),
(37, 22, '127.0.0.1', '2025-08-27 07:28:50'),
(38, 22, '127.0.0.1', '2025-08-27 07:29:35'),
(39, 22, '127.0.0.1', '2025-08-27 07:30:57'),
(40, 22, '127.0.0.1', '2025-08-27 07:31:43'),
(41, 22, '127.0.0.1', '2025-08-27 07:33:19'),
(42, 22, '127.0.0.1', '2025-08-27 07:34:41'),
(43, 22, '127.0.0.1', '2025-08-27 07:36:03'),
(44, 22, '127.0.0.1', '2025-08-27 07:39:43'),
(45, 19, '127.0.0.1', '2025-08-27 07:45:23'),
(46, 21, '127.0.0.1', '2025-08-27 08:13:39'),
(47, 20, '127.0.0.1', '2025-08-27 08:15:34'),
(48, 20, '127.0.0.1', '2025-08-27 08:23:41'),
(49, 20, '127.0.0.1', '2025-08-27 08:23:56'),
(50, 20, '127.0.0.1', '2025-08-27 08:24:22'),
(51, 20, '127.0.0.1', '2025-08-27 08:24:40'),
(52, 20, '127.0.0.1', '2025-08-27 08:25:04'),
(53, 16, '127.0.0.1', '2025-08-28 05:22:40'),
(54, 15, '127.0.0.1', '2025-08-28 05:23:52'),
(55, 21, '127.0.0.1', '2025-08-28 05:25:46'),
(56, 19, '127.0.0.1', '2025-08-28 05:39:32'),
(57, 16, '127.0.0.1', '2025-09-01 06:03:31'),
(58, 15, '127.0.0.1', '2025-09-01 06:08:21'),
(59, 13, '127.0.0.1', '2025-09-01 06:08:59'),
(60, 21, '127.0.0.1', '2025-09-01 06:35:19'),
(61, 22, '127.0.0.1', '2025-09-02 06:53:07'),
(62, 22, '127.0.0.1', '2025-09-02 06:54:24'),
(63, 22, '127.0.0.1', '2025-09-02 07:21:43'),
(64, 13, '127.0.0.1', '2025-09-02 07:23:44');

-- --------------------------------------------------------

--
-- Table structure for table `project`
--

CREATE TABLE `project` (
  `p_id` int(11) NOT NULL,
  `p_name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `a_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `p_image` varchar(255) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `project`
--

INSERT INTO `project` (`p_id`, `p_name`, `description`, `a_id`, `created_at`, `updated_at`, `p_image`, `address`) VALUES
(2, 'บุรีรัมย์', 'Luxury condos in the heart of the city.', 4, '2025-05-22 08:59:21', '2025-08-21 13:44:40', 'OIP_1.webp', 'ในมือง บุรีรัมย์'),
(3, 'กาฬสินธุ์', 'Eco-friendly homes with large green spaces.', 4, '2025-05-22 08:59:21', '2025-08-26 11:35:17', 'istockphoto-1270000116-612x612_1.jpg', 'ในมือง กาฬสินธุ์'),
(6, 'ขอนแก่น', 'โปรโมชั่นจากโครงการ', 6, '2025-05-28 05:05:07', '2025-08-27 07:08:15', 'Khon-Kaen-1.jpg', 'ในเมือง ขอนแก่น');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `house`
--
ALTER TABLE `house`
  ADD PRIMARY KEY (`h_id`),
  ADD KEY `house_ibfk_1` (`t_id`),
  ADD KEY `f_id` (`f_id`);

--
-- Indexes for table `house_features`
--
ALTER TABLE `house_features`
  ADD PRIMARY KEY (`f_id`);

--
-- Indexes for table `house_images`
--
ALTER TABLE `house_images`
  ADD PRIMARY KEY (`id`),
  ADD KEY `house_id` (`house_id`);

--
-- Indexes for table `house_type`
--
ALTER TABLE `house_type`
  ADD PRIMARY KEY (`t_id`);

--
-- Indexes for table `house_views`
--
ALTER TABLE `house_views`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_house_views_created_at` (`created_at`),
  ADD KEY `idx_house_views_house_id` (`house_id`);

--
-- Indexes for table `project`
--
ALTER TABLE `project`
  ADD PRIMARY KEY (`p_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `house`
--
ALTER TABLE `house`
  MODIFY `h_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT for table `house_features`
--
ALTER TABLE `house_features`
  MODIFY `f_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `house_images`
--
ALTER TABLE `house_images`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=92;

--
-- AUTO_INCREMENT for table `house_type`
--
ALTER TABLE `house_type`
  MODIFY `t_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `house_views`
--
ALTER TABLE `house_views`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=65;

--
-- AUTO_INCREMENT for table `project`
--
ALTER TABLE `project`
  MODIFY `p_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `house`
--
ALTER TABLE `house`
  ADD CONSTRAINT `house_ibfk_1` FOREIGN KEY (`t_id`) REFERENCES `house_type` (`t_id`) ON DELETE SET NULL,
  ADD CONSTRAINT `house_ibfk_2` FOREIGN KEY (`f_id`) REFERENCES `house_features` (`f_id`) ON DELETE SET NULL;

--
-- Constraints for table `house_images`
--
ALTER TABLE `house_images`
  ADD CONSTRAINT `house_images_ibfk_1` FOREIGN KEY (`house_id`) REFERENCES `house` (`h_id`) ON DELETE CASCADE;

--
-- Constraints for table `house_views`
--
ALTER TABLE `house_views`
  ADD CONSTRAINT `fk_house_views_house` FOREIGN KEY (`house_id`) REFERENCES `house` (`h_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
