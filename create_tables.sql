CREATE TABLE IF NOT EXISTS users(
       username VARCHAR(20) PRIMARY KEY,
       email VARCHAR(80),
       realname VARCHAR(80),

       password_hash CHAR(88) CHARACTER SET latin1,
       salt CHAR(43) CHARACTER SET latin1 NOT NULL,
       work_factor INT NOT NULL DEFAULT 15,

       privs ENUM('user', 'admin') NOT NULL DEFAULT 'user',
       INDEX ( email )
);

