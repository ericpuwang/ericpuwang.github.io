---
title: 基于CentOS7安装LNMP套件
date: 2017-11-24
tags:
- linux
- nginx
- mysql
- php
categories: linux
---

# 安装依赖包
```shell
yum install -y wget gcc gcc-c++ make curl curl-devel libxml2 libxml2-devel \
libjpeg libjpeg-devel libpng libpng-devel libmcrypt libmcrypt-devel zlib \
zlib-devel openssl openssl-devel freetype freetype-devel gd gd-devel perl \
perl-devel ncurses ncurses-devel bison bison-devel libtool gettext \
gettext-devel cmake pcre pcre-devel
```

# 下载nginx、php、mysql源码包

> `wget -O nginx-1.13.7.tar.gz http://nginx.org/download/nginx-1.13.7.tar.gz`

> `wget -O php-5.6.32.tar.gz http://am1.php.net/distributions/php-5.6.32.tar.gz`

> `wget -O mysql-5.6.38.tar.gz https://cdn.mysql.com//Downloads/MySQL-5.6/mysql-5.6.38.tar.gz`

# 解压

```shell
tar zxvf nginx-1.13.7.tar.gz
tar zxvf php-5.6.32.tar.gz
tar zxvf mysql-5.6.38.tar.gz
```

# 安装nginx

### 编译
```shell
cd nginx-1.13.7

./configure --prefix=/usr/local/nginx

make && make install
```

### 添加环境变量
```shell
# vim ~/.bash_profile
NGINX_HOME=/usr/local/nginx
PATH=$PATH:$NGINX_HOME/sbin
export PATH
```

# 安装mysql

### 编译
```shell
cd mysql-5.6.38

cmake -DCMAKE_INSTALL_PREFIX=/usr/local/mysql \
-DMYSQL_DATADIR=/usr/local/mysql/data \
-DMYSQL_UNIX_ADDR=/usr/local/mysql/mysql.sock \
-DSYSCONFDIR=/usr/local/mysql \
-DWITH_MYISAM_STORAGE_ENGINE=1 \
-DWITH_ARCHIVE_STORAGE_ENGINE=1 \
-DWITH_BLACKHOLE_STORAGE_ENGINE=1 \
-DWITH_INNOBASE_STORAGE_ENGINE=1 \
-DWITH_MEMORY_STORAGE_ENGINE=1 \
-DWITH_READLINE=1 \
-DMYSQL_TCP_PORT=3306 \
-DENABLED_LOCAL_INFILE=1 \
-DWITH_PARTITION_STORAGE_ENGINE=1 \
-DEXTRA_CHARSETS=all \
-DDEFAULT_CHARSET=utf8 \
-DDEFAULT_COLLATION=utf8_general_ci

make && make install
```

### 添加环境变量
```shell
# vim ~/.bash_profile
MYSQL_HOME=/usr/local/mysql
PATH=$PATH:$MYSQL_HOME/bin
export PATH
```

### 添加mysql用户
`useradd -s /sbin/nologin mysql`

### mysql目录授权
`chown -R mysql:mysql /usr/local/mysql`

### 初始化数据库

- 进入安装目录
    `cd /usr/local/mysql/scripts`
- 数据库初始化
```shell
./mysql_install_db \
--basedir=/usr/local/mysql \
--datadir=/usr/local/mysql/data \
--user=mysql
```
- 设置开机启动
```shell
cp /usr/local/mysql/support-files/mysql.server /etc/init.d/mysqld
cd /etc/init.d/mysqld

# vim mysqld
chkconfig:2345 80 90

chkconfig --add mysqld
```
- 用户初始化
```shell
/etc/init.d/mysqld start
    
mysql_secure_installation # 设置数据库root用户和密码
```
# 安装php

### 编译
```shell
cd php-5.6.32

./configure --prefix=/usr/local/php --with-config-file-path=/usr/local/php \
--enable-opcache --enable-fpm --with-fpm-user=www-data --with-fpm-group=www-data \
--with-mysql=mysqlnd --with-mysqli=mysqlnd --with-pdo-mysql=mysqlnd \
--with-curl --enable-mbstring=all --with-iconv --with-mhash --with-mcrypt \
--with-gd --with-openssl --enable-sockets --with-gettext --with-zlib \
--enable-zip --enable-soap --with-libxml-dir --with-png-dir \
--with-jpeg-dir --with-freetype-dir --enable-ftp --with-xmlrpc

make && make install
```

### 环境变量
```shell
# vim ~/.bash_profile
PHP_HOME=/usr/local/php
PATH=$PATH:$PHP_HOME/bin:$PHP_HOME/sbin
export PATH
```

### php环境设置
`cp php-5.6.32/php.ini-production /usr/local/php/php.ini`

### 环境测试
```php
# vim phpinfo.php
<?php
    phpinfo();
?>

php phpinfo.php
```

### php扩展
**phpize是用来扩展php扩展模块的，即不用重新编译PHP，通过phpize就可以建立php的外挂模块**
1. 进入php安装包目录
```shell
cd php-5.6.32/ext
```

2. 选择并编译扩展[eg:`curl`]
```shell
cd curl
    
phpize ./configure --with-php-config=/usr/local/php/bin/php-config
    
make && make install
```

3. 安装扩展
```shell
#vim /usr/local/php/php.ini
# 写入下面的配置信息
    
extension=/usr/local/php/lib/php/extensions/no-debug-non-zts-20131226/curl.so
```