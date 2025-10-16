<?php
# CMS Made Simple Configuration File
$config['dbms'] = 'mysqli';
$config['db_hostname'] = 'mysql';
$config['db_username'] = 'root';
$config['db_password'] = 'root';
$config['db_name'] = 'cmsms';
$config['db_prefix'] = 'cms_';
$config['timezone'] = 'UTC';

if (isset($_SERVER['HTTP_HOST'])) {
    $config['root_url'] = 'http://' . $_SERVER['HTTP_HOST'];
}