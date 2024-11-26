CREATE DATABASE IF NOT EXISTS `nutrigood-database` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `nutrigood-database`;

CREATE TABLE `users` (
  `id` VARCHAR(64) PRIMARY KEY,
  `email` VARCHAR(100) UNIQUE NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `age` int NOT NULL DEFAULT '0',
  `diabetes` tinyint(1) NOT NULL DEFAULT '1',
  `createdAt` DATETIME NOT NULL
);
CREATE TABLE `products` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `userId` VARCHAR(50) NOT NULL,
  `namaProduct` VARCHAR(100) NOT NULL,
  `valueProduct` FLOAT NOT NULL,
  `createdAt` DATETIME NOT NULL,
  FOREIGN KEY (userId) REFERENCES users(id)
); 

