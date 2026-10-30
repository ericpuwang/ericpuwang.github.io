# CentOS-LDAP统一认证登陆

> 安装nss-pam-ldapd

## 图形化部署

```shell
authconfig-tui

选择 Use LDAP、Use LDAP Authentication
```
 

## 配置文件部署

**/etc/openldap/ldap.conf**

```shell
BASE dc=periky,dc=com
URI ldap://127.0.0.1/
```

**/etc/nsswitch.conf**

> 此三项后面加上ldap

```shell
# Example:
#passwd:    db files nisplus nis
#shadow:    db files nisplus nis
#group:     db files nisplus nis

passwd:     files sss ldap
shadow:     files sss ldap
group:      files sss ldap
```

**/etc/nslcd.conf**

```shell
uri ldap://127.0.0.1/   # 修改为ldap服务端ip
base dc=periky,dc=com   # 更新为ldap的basedn
# 追加下面两行
ssl no
tls_cacertdir /etc/openldap/cacerts
```

**/etc/pam.d/system-auth**

```shell
#%PAM-1.0
# This file is auto-generated.
# User changes will be destroyed the next time authconfig is run.
auth        required      pam_env.so
auth        sufficient    pam_unix.so nullok try_first_pass
auth        requisite     pam_succeed_if.so uid >= 1000 quiet_success
auth        sufficient    pam_ldap.so use_first_pass   # 添加此行
auth        required      pam_deny.so

account     required      pam_unix.so broken_shadow
account     sufficient    pam_localuser.so
account     sufficient    pam_succeed_if.so uid < 1000 quiet
account     [default=bad success=ok user_unknown=ignore] pam_ldap.so   # 添加此行
account     required      pam_permit.so

password    requisite     pam_pwquality.so try_first_pass local_users_only retry=3 authtok_type=
password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok
password    sufficient    pam_ldap.so use_authtok   # 添加此行
password    required      pam_deny.so

session     optional      pam_keyinit.so revoke
session     required      pam_limits.so
-session     optional      pam_systemd.so
session     [success=1 default=ignore] pam_succeed_if.so service in crond quiet use_uid
session     required      pam_unix.so
session     optional      pam_ldap.so  # 添加此行
```

**/etc/ssh/sshd_config**

```shell
PasswordAuthentication yes
UsePAM yes
```

## 重启服务

```shell
systemctl restart nslcd
systemctl restart sshd
```