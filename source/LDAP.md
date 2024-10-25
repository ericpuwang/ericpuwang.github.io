---
title: 安装LDAP
date: 2019-07-21
tags:
- linux
- ldap
categories: linux
---

# 前提条件

- 关闭防火墙
- 关闭selinux


# 安装ldap

```shell
yum install openldap openldap-clients openldap-servers
```

# 设置管理员密码

```shell
slappasswd
```

# 设置ldap数据库
```shell
cp /usr/share/openldap-servers/DB_CONFIG.example /var/lib/ldap/DB_CONFIG
chown ldap:ldap /var/lib/ldap/*
```

# 启动ldap服务，并设置为开机启动
```shell
systemctl start slapd
systemctl enable slapd
```

# 配置ldap server

**切换到ldap目录**
`cd /etc/openldap/slapd.d/cn=config`

**更新hdb.ldif**
* `更新my-domain为自定义的名称`
* 添加`olcRootPW`,它的内容是上面创建的管理员密码
> 例如，这里更新为periky

```shell
cat <<EOF | ldapadd -Y EXTERNAL -H ldapi:///
dn: olcDatabase={2}hdb,cn=config
changetype: modify
delete: olcSuffix

dn: olcDatabase={2}hdb,cn=config
changetype: modify
add: olcSuffix
olcSuffix: dc=periky,dc=com

dn: olcDatabase={2}hdb,cn=config
changetype: modify
delete: olcRootDN

dn: olcDatabase={2}hdb,cn=config
changetype: modify
add: olcRootDN
olcRootDN: cn=Admin,dc=periky,dc=com

dn: olcDatabase={2}hdb,cn=config
changetype: modify
add: olcRootPW
olcRootPW: {SSHA}V1MUM1xql6pN3t3fMiSb4tYk5L6cZFXn
EOF
```

**更新monitor.ldif**
```shell
cat <<EOF | ldapadd -Y EXTERNAL -H ldapi:///
dn: olcDatabase={1}monitor,cn=config
changetype: modify
delete: olcAccess

dn: olcDatabase={1}monitor,cn=config
changetype: modify
add: olcAccess
olcAccess: {0}to * by dn.base="gidNumber=0+uidNumber=0,cn=peercred,cn=extern al,cn=auth" read by dn.base="cn=Admin,dc=periky,dc=com" read by * none
EOF
```

# 配置信息测试
```shell
slaptest -u
```
* 输出内容 config file testing succeeded

# 添加ldap schema
```shell
ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/cosine.ldif
ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/nis.ldif
ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/inetorgperson.ldif
```

# 创建ldap目录
> 文件名`base.ldif`,文件路径`/root/ldap`

```shell
dn: dc=periky,dc=com
dc: periky
objectClass: top
objectClass: domain

dn: cn=Admin,dc=periky,dc=com
objectClass: organizationalRole
cn: Admin
description: LDAP Manager

dn: ou=Account,dc=periky,dc=com
objectClass: organizationalUnit
ou: Account
```

* 执行命令`ldapadd -x -W -D "cn=Admin,dc=periky,dc=com" -f /root/ldap/base.ldif`

# 添加用户
> 文件名`test.ldif`,文件路径`/root/ldap`

```shell
dn: cn=test,ou=Account,dc=periky,dc=com
cn: test
gidnumber: 10000
homedirectory: /home/dev
loginshell: /bin/bash
objectclass: posixAccount
objectclass: inetOrgPerson
objectclass: organizationalPerson
objectclass: person
sn: test
uid: test
uidnumber: 10001
```

* `ldapadd -x -W -D "cn=Admin,dc=periky,dc=com" -f /root/ldap/test.ldif`
