<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

$report = array();

$report['php_version'] = PHP_VERSION;
$report['cwd'] = getcwd();

function exists($p){ return file_exists($p) ? 'yes' : 'no'; }
$report['paths'] = array(
  'index.php' => exists('index.php'),
  'session.php' => exists('session.php'),
  'media' => exists('media'),
  'media/photos' => exists('media/photos'),
  'media/videos' => exists('media/videos'),
  'assets/css/style.css' => exists('assets/css/style.css'),
  'assets/img/video_fallback.png' => exists('assets/img/video_fallback.png'),
);

function list_dir($dir){
  $out = array();
  if (!is_dir($dir)) return $out;
  $d = opendir($dir);
  if (!$d) return $out;
  while (($f = readdir($d)) !== false) {
    if ($f=='.'||$f=='..') continue;
    $p = $dir.'/'.$f;
    $out[] = array('name'=>$f,'is_file'=>is_file($p),'mtime'=>@filemtime($p));
  }
  closedir($d);
  return $out;
}

$report['photos_list'] = list_dir('media/photos');
$report['videos_list'] = list_dir('media/videos');

header('Content-Type: application/json');
echo json_encode($report, JSON_PRETTY_PRINT);
