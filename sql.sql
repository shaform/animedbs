-- -----------------------------------------------------
-- Table `animedb`.`USER`
-- -----------------------------------------------------
CREATE  TABLE `USER` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Email` VARCHAR(256) NOT NULL,
  `Nickname` VARCHAR(30) NOT NULL,
  `Gender` ENUM('female','male','other') NOT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE INDEX `Email_UNIQUE` (`Email` ASC)
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;

-- -----------------------------------------------------
-- Table `animedb`.`AUTHOR`
-- -----------------------------------------------------
CREATE  TABLE `AUTHOR` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Name` VARCHAR(30) NOT NULL,
  `Description` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`ANIME`
-- -----------------------------------------------------
CREATE  TABLE `ANIME` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Title` VARCHAR(100) NOT NULL,
  `Authored_by` INT NOT NULL,
  `Description` TEXT NULL,
  `Web_address` VARCHAR(512) NULL,
  PRIMARY KEY (`Id`),
  INDEX `fk_ANIME_1` (`Authored_by` ASC),
  UNIQUE INDEX `Title_UNIQUE` (`Title` ASC),
  CONSTRAINT `fk_ANIME_1`
    FOREIGN KEY (`Authored_by`)
    REFERENCES `animedb`.`AUTHOR` (`Id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`SEASON`
-- -----------------------------------------------------
CREATE  TABLE `SEASON` (
  `Part_of` INT NOT NULL,
  `Series_num` INT NOT NULL,
  `Full_name` VARCHAR(100) NOT NULL,
  `Total_episodes` INT NOT NULL,
  `Release_year` YEAR NOT NULL,
  `Release_month` TINYINT NOT NULL,
  INDEX `fk_SEASON_1` (`Part_of` ASC),
  PRIMARY KEY (`Part_of`, `Series_num`),
  CONSTRAINT `fk_SEASON_1`
    FOREIGN KEY (`Part_of`)
    REFERENCES `animedb`.`ANIME` (`Id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CHECK (Release_month >= 1),
  CHECK (Release_month <= 12)
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`SEIYU`
-- -----------------------------------------------------
CREATE  TABLE `SEIYU` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Name` VARCHAR(30) NOT NULL,
  `Gender` ENUM('female','male') NULL,
  `Birthday` DATE NULL,
  `Description` TEXT NULL,
  PRIMARY KEY (`Id`)
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`CHARACTER`
-- -----------------------------------------------------
CREATE  TABLE `CHARACTER` (
  `Present_in` INT NOT NULL,
  `Name` VARCHAR(30) NOT NULL,
  `Gender` ENUM('female','male','秀吉') NULL,
  `Voiced_by` INT NOT NULL,
  `Description` TEXT NULL,
  PRIMARY KEY (`Present_in`, `Name`),
  INDEX `fk_CHARACTER_1` (`Present_in` ASC),
  INDEX `fk_CHARACTER_2` (`Voiced_by` ASC),
  CONSTRAINT `fk_CHARACTER_1`
    FOREIGN KEY (`Present_in`)
    REFERENCES `animedb`.`ANIME` (`Id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_CHARACTER_2`
    FOREIGN KEY (`Voiced_by`)
    REFERENCES `animedb`.`SEIYU` (`Id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`COMMENTS_ON`
-- -----------------------------------------------------
CREATE  TABLE `COMMENTS_ON` (
  `Commenter` INT NOT NULL,
  `Commentee_anime` INT NOT NULL,
  `Commentee_season` INT NOT NULL,
  `Rating` TINYINT NOT NULL,
  `Text` VARCHAR(1000) NOT NULL,
  `Datetime` TIMESTAMP NOT NULL,
  PRIMARY KEY (`Commentee_season`, `Commentee_anime`, `Commenter`),
  INDEX `fk_COMMENT_1` (`Commentee_anime` ASC, `Commentee_season` ASC),
  INDEX `fk_COMMENT_2` (`Commenter` ASC),
  CONSTRAINT `fk_COMMENT_1`
    FOREIGN KEY (`Commentee_anime` , `Commentee_season`)
    REFERENCES `animedb`.`SEASON` (`Part_of` , `Series_num`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_COMMENT_2`
    FOREIGN KEY (`Commenter`)
    REFERENCES `animedb`.`USER` (`Id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CHECK (Rating >=1 AND Rating <= 12)
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`SONG`
-- -----------------------------------------------------
CREATE  TABLE `SONG` (
  `Id` INT NOT NULL AUTO_INCREMENT,
  `Featured_in_aid` INT NOT NULL,
  `Featured_in_snum` INT NOT NULL,
  `Singed_by` INT NOT NULL,
  `Type` ENUM('op','ed') NOT NULL,
  `Title` VARCHAR(100) NOT NULL,
  `Lyrics` TEXT NULL,
  PRIMARY KEY (`Id`),
  INDEX `fk_SONG_1` (`Featured_in_aid` ASC, `Featured_in_snum` ASC),
  INDEX `fk_SONG_2` (`Singed_by` ASC),
  CONSTRAINT `fk_SONG_1`
    FOREIGN KEY (`Featured_in_aid` , `Featured_in_snum`)
    REFERENCES `animedb`.`SEASON` (`Part_of` , `Series_num`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_SONG_2`
    FOREIGN KEY (`Singed_by`)
    REFERENCES `animedb`.`SEIYU` (`Id`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`CHARACTER_IMAGE`
-- -----------------------------------------------------
CREATE  TABLE `CHARACTER_IMAGE` (
  `Character_anime` INT NOT NULL ,
  `Character_name` VARCHAR(30) NOT NULL,
  `Address` VARCHAR(256) NOT NULL,
  PRIMARY KEY (`Character_anime`, `Character_name`, `Address`) ,
  INDEX `fk_CHARACTER_IMAGE_1` (`Character_anime` ASC, `Character_name` ASC, `Address` ASC),
  CONSTRAINT `fk_CHARACTER_IMAGE_1`
    FOREIGN KEY (`Character_anime` , `Character_name`)
    REFERENCES `animedb`.`CHARACTER` (`Present_in` , `Name`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `animedb`.`ANIME_IMAGE`
-- -----------------------------------------------------
CREATE  TABLE `ANIME_IMAGE` (
  `Anime_id` INT NOT NULL,
  `Address` VARCHAR(256) NOT NULL,
  PRIMARY KEY (`Anime_id`, `Address`),
  INDEX `fk_CHARACTER_IMAGE_1` (`Anime_id` ASC, `Address` ASC),
  CONSTRAINT `fk_CHARACTER_IMAGE_10`
    FOREIGN KEY (`Anime_id`)
    REFERENCES `animedb`.`ANIME` (`Id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB, ROW_FORMAT=COMPRESSED, DEFAULT CHARACTER SET = utf8;
