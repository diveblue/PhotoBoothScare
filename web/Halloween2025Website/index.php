<?php
// Widowmont Drive Church of the Unholy - Halloween Photo Gallery
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

function h($s) { 
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); 
}

function list_files_by_ext($dir, $exts) {
    $out = [];
    if (!is_dir($dir)) return $out;
    $dh = opendir($dir);
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

function build_sessions() {
    $photos = list_files_by_ext('media/photos', ['jpg', 'jpeg', 'png', 'webp', 'gif']);
    $videos = list_files_by_ext('media/videos', ['mp4', 'mov', 'webm', 'mkv']);
    $sessions = [];
    $pat = '/^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([A-Za-z0-9\-_]+)_(.+)\.([A-Za-z0-9]+)$/';
    
    foreach ($photos as $p) {
        $b = basename($p);
        if (!preg_match($pat, $b, $m)) continue;
        $k = $m[1] . '_' . $m[2];
        if (!isset($sessions[$k])) {
            $sessions[$k] = [
                'ts' => $m[1], 
                'session' => $m[2], 
                'items' => [],
                'photo_count' => 0,
                'video_count' => 0
            ];
        }
        $sessions[$k]['items'][] = ['type' => 'photo', 'path' => $p, 'mtime' => filemtime($p)];
        $sessions[$k]['photo_count']++;
    }
    
    foreach ($videos as $v) {
        $b = basename($v);
        if (!preg_match($pat, $b, $m)) continue;
        $k = $m[1] . '_' . $m[2];
        if (!isset($sessions[$k])) {
            $sessions[$k] = [
                'ts' => $m[1], 
                'session' => $m[2], 
                'items' => [],
                'photo_count' => 0,
                'video_count' => 0
            ];
        }
        $sessions[$k]['items'][] = ['type' => 'video', 'path' => $v, 'mtime' => filemtime($v)];
        $sessions[$k]['video_count']++;
    }
    
    // Sort sessions by newest first
    usort($sessions, function($a, $b) {
        $ma = max(array_map(fn($i) => $i['mtime'], $a['items']));
        $mb = max(array_map(fn($i) => $i['mtime'], $b['items']));
        return $mb <=> $ma;
    });
    
    return $sessions;
}

function format_date($timestamp_str) {
    $dt = DateTime::createFromFormat('Y-m-d_H-i-s', $timestamp_str);
    return $dt ? $dt->format('M j, Y • g:i A') : $timestamp_str;
}

$sessions = build_sessions();
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Widowmont Drive Church of the Unholy - Halloween Gallery</title>
    <link rel="stylesheet" href="assets/css/style.css?v=<?php echo filemtime('assets/css/style.css'); ?>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Butcherman&family=Nosifer&family=Creepster&family=Chiller:wght@400&display=swap" rel="stylesheet">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <h1 class="site-title">
                <span class="skull">☠</span>
                Widowmont Drive Church of the Unholy
                <span class="skull">☠</span>
            </h1>
            <p class="site-tagline">Halloween Photo Gallery • Embrace the Darkness</p>
        </div>
    </header>

    <main class="container">
        <?php if (!$sessions): ?>
        <div class="empty-state">
            <div class="empty-icon">🦇</div>
            <h2>The Darkness Awaits</h2>
            <p>No souls have been captured yet. Check back soon...</p>
        </div>
        <?php else: ?>
        <div class="sessions-header">
            <h2>🎭 Recent Sessions</h2>
            <p><?php echo count($sessions); ?> dark encounters captured</p>
        </div>
        
        <div class="sessions-grid">
            <?php foreach ($sessions as $s): 
                $rep = 'assets/img/video_fallback.png';
                foreach ($s['items'] as $i) {
                    if ($i['type'] === 'photo') { 
                        $rep = $i['path']; 
                        break; 
                    }
                }
                $key = $s['ts'] . '_' . $s['session'];
                $total_items = $s['photo_count'] + $s['video_count'];
            ?>
            <a class="session-card" href="session.php?key=<?php echo urlencode($key); ?>">
                <div class="session-thumbnail">
                    <img src="<?php echo h($rep); ?>" alt="Session <?php echo h($s['session']); ?>" loading="lazy">
                    <div class="session-overlay">
                        <div class="session-stats">
                            <?php if ($s['photo_count'] > 0): ?>
                            <span class="stat">📸 <?php echo $s['photo_count']; ?></span>
                            <?php endif; ?>
                            <?php if ($s['video_count'] > 0): ?>
                            <span class="stat">🎬 <?php echo $s['video_count']; ?></span>
                            <?php endif; ?>
                        </div>
                        <div class="view-session">View Session →</div>
                    </div>
                </div>
                <div class="session-info">
                    <div class="session-title">Session <?php echo h($s['session']); ?></div>
                    <div class="session-date"><?php echo format_date($s['ts']); ?></div>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>🕯️ Widowmont Drive Church of the Unholy • Halloween <?php echo date('Y'); ?> 🕯️</p>
            <p class="footer-tagline">Where darkness meets devotion</p>
        </div>
    </footer>
</body>
</html>
