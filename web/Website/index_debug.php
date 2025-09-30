<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

function h($s){ return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
function list_files_by_ext($dir, $exts) {
  $out = array();
  if (!is_dir($dir)) { echo "<p>DEBUG: dir not found: ".h($dir)."</p>"; return $out; }
  $dh = opendir($dir);
  if (!$dh) { echo "<p>DEBUG: opendir failed for ".h($dir)."</p>"; return $out; }
  while (($f = readdir($dh)) !== false) {
    if ($f === '.' || $f === '..') continue;
    $path = $dir . '/' . $f;
    if (!is_file($path)) continue;
    $ext = strtolower(pathinfo($f, PATHINFO_EXTENSION));
    if (in_array($ext, $exts, true)) { $out[] = $path; }
  }
  closedir($dh);
  return $out;
}

function build_sessions() {
  $photos = list_files_by_ext('media/photos', array('jpg','jpeg','png','webp','gif'));
  $videos = list_files_by_ext('media/videos', array('mp4','mov','webm','mkv'));
  echo "<p>DEBUG: photos=".count($photos)." videos=".count($videos)."</p>";
  $sessions = array();
  $pattern = '/^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([A-Za-z0-9\-_]+)_(.+)\.([A-Za-z0-9]+)$/';

  foreach ($photos as $p) {
    $base = basename($p);
    if (preg_match($pattern, $base, $m)) { $ts=$m[1]; $sess=$m[2]; }
    else { $ts='unknown'; $sess='unknown'; echo "<p>DEBUG: photo unmatched filename: ".h($base)."</p>"; }
    $key = $ts.'_'.$sess;
    if (!isset($sessions[$key])) $sessions[$key] = array('ts'=>$ts,'session'=>$sess,'items'=>array());
    $sessions[$key]['items'][] = array('type'=>'photo','path'=>$p,'mtime'=>@filemtime($p));
  }
  foreach ($videos as $v) {
    $base = basename($v);
    if (preg_match($pattern, $base, $m)) { $ts=$m[1]; $sess=$m[2]; }
    else { $ts='unknown'; $sess='unknown'; echo "<p>DEBUG: video unmatched filename: ".h($base)."</p>"; }
    $key = $ts.'_'.$sess;
    if (!isset($sessions[$key])) $sessions[$key] = array('ts'=>$ts,'session'=>$sess,'items'=>array());
    $sessions[$key]['items'][] = array('type'=>'video','path'=>$v,'mtime'=>@filemtime($v));
  }

  $arr = array_values($sessions);
  usort($arr, function($a,$b){
    $ma = 0; foreach ($a['items'] as $it) { $ma = max($ma, intval($it['mtime'])); }
    $mb = 0; foreach ($b['items'] as $it) { $mb = max($mb, intval($it['mtime'])); }
    return $mb - $ma;
  });
  return $arr;
}

echo "<h3>DEBUG: cwd=".h(getcwd())."</h3>";
$sessions = build_sessions();
?>
<!doctype html><html><head><meta charset="utf-8"><title>index_debug</title></head><body>
<h1>Index Debug</h1>
<?php if (!$sessions): ?>
  <p>No sessions.</p>
<?php else: ?>
  <ul>
  <?php foreach ($sessions as $sess): 
    $key = (($sess['ts']!=='unknown')?$sess['ts']:'unknown') . '_' . (($sess['session'])?$sess['session']:'nosession');
    $title = (($sess['ts']!=='unknown')?$sess['ts']:'Unknown time');
    $subtitle = (($sess['session'])?$sess['session']:'No Session');
  ?>
    <li>
      <a href="session_debug.php?key=<?=h(urlencode($key))?>"><?=h($title)?> — <?=h($subtitle)?></a>
      (items: <?=count($sess['items'])?>)
    </li>
  <?php endforeach; ?>
  </ul>
<?php endif; ?>
</body></html>
