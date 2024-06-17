SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;

DROP TABLE IF EXISTS `sub_channel`;
CREATE TABLE `sub_channel` (
  `id` int NOT NULL,
  `subreddit` varchar(64) NOT NULL,
  `channel_id` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE `sub_channel`
  ADD PRIMARY KEY (`id`);


ALTER TABLE `sub_channel`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=126;
COMMIT;
