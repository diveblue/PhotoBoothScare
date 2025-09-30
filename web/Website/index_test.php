<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

function h($s){ return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
function list_files_by_ext($dir, $exts) {
  $out = [];
  if (!is_dir($dir)) { echo "<p>DEBUG: missing dir: ".h($dir)."</p>"; return $out; }
  $dh = opendir($dir);
  if (!$dh) { echo "<p>DEBUG: cannot open dir: ".h($dir)."</p>"; return $out; }
  while (($f = readdir($dh)) !== false) {
    if ($f === '.' || $f === '..') continue;
    $p = $dir . '/' . $f;
    if (!is_file($p)) continue;
    $ext = strtolower(pathinfo($f, PATHINFO_EXTENSION));
    if (in_array($ext, $exts, true)) $out[] = $p;
  }
  closedir($dh);
  return $out;
}

$photos = list_files_by_ext('media/photos', ['jpg','jpeg','png','webp','gif']);
$videos = list_files_by_ext('media/videos', ['mp4','mov','webm','mkv']);

echo "<h3>Photos: ".count($photos)." — Videos: ".count($videos)."</h3>";

$pattern = '/^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([A-Za-z0-9\-_]+)_(.+)\.([A-Za-z0-9]+)$/';
$sessions = [];
foreach ($photos as $p) {
  $b = basename($p);
  if (preg_match($pattern, $b, $m)) {
    $key = $m[1].'_'.$m[2];
    $sessions[$key]['ts'] = $m[1];
    $sessions[$key]['session'] = $m[2];
    $sessions[$key]['items'][] = ['type'=>'photo','path'=>$p,'mtime'=>@filemtime($p)];
  } else {
    echo "<p>DEBUG unmatched photo: ".h($b)."</p>";
  }
}
foreach ($videos as $v) {
  $b = basename($v);
  if (preg_match($pattern, $b, $m)) {
    $key = $m[1].'_'.$m[2];
    $sessions[$key]['ts'] = $m[1];
    $sessions[$key]['session'] = $m[2];
    $sessions[$key]['items'][] = ['type'=>'video','path'=>$v,'mtime'=>@filemtime($v)];
  } else {
    echo "<p>DEBUG unmatched video: ".h($b)."</p>";
  }
}

$sessions = array_values($sessions);
usort($sessions, function($a,$b){
  $ma = 0; foreach (($a['items'] ?? []) as $it) $ma = max($ma, (int)($it['mtime'] ?? 0));
  $mb = 0; foreach (($b['items'] ?? []) as $it) $mb = max($mb, (int)($it['mtime'] ?? 0));
  return $mb <=> $ma;
});

echo "<ul>";
foreach ($sessions as $s) {
  $key = $s['ts'].'_'.$s['session'];
  echo "<li>".h($key)." — items: ".count($s['items'])."</li>";
}
echo "</ul>";
