<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
function h($s){ return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
function list_files($dir){
  $out = array();
  if (!is_dir($dir)) return $out;
  $d = opendir($dir);
  if (!$d) return $out;
  while (($f=readdir($d))!==false){ if($f==='.'||$f==='..') continue; if(is_file($dir.'/'.$f)) $out[]=$f; }
  closedir($d);
  sort($out);
  return $out;
}
$photos = list_files('media/photos');
$videos = list_files('media/videos');
?><!doctype html><html><head><meta charset="utf-8"><title>index_plain</title></head><body>
<h1>index_plain</h1>
<h2>photos</h2>
<ul><?php foreach($photos as $f): ?><li><a href="<?=h('media/photos/'.$f)?>"><?=h($f)?></a></li><?php endforeach;?></ul>
<h2>videos</h2>
<ul><?php foreach($videos as $f): ?><li><a href="<?=h('media/videos/'.$f)?>"><?=h($f)?></a></li><?php endforeach;?></ul>
</body></html>
