<?php
// Widowmont Drive Church of the Unholy - Session Viewer
ini_set('display_errors', 1);
error_reporting(E_ALL);

function h($s) { 
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); 
}

function list_files_by_ext($d, $e) {
    $o = [];
    if (!is_dir($d)) return $o;
    $dh = opendir($d);
    while (($f = readdir($dh)) !== false) {
        if ($f === '.' || $f === '..') continue;
        $p = $d . '/' . $f;
        if (!is_file($p)) continue;
        $x = strtolower(pathinfo($f, PATHINFO_EXTENSION));
        if (in_array($x, $e, true)) $o[] = $p;
    }
    closedir($dh);
    return $o;
}

function build_sessions() {
    $p = list_files_by_ext('media/photos', ['jpg', 'jpeg', 'png', 'webp', 'gif']);
    $v = list_files_by_ext('media/videos', ['mp4', 'mov', 'webm', 'mkv']);
    $s = [];
    $pat = '/^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([A-Za-z0-9\-_]+)_(.+)\.([A-Za-z0-9]+)$/';
    
    foreach ($p as $f) {
        $b = basename($f);
        if (!preg_match($pat, $b, $m)) continue;
        $k = $m[1] . '_' . $m[2];
        if (!isset($s[$k])) {
            $s[$k] = [
                'ts' => $m[1], 
                'session' => $m[2], 
                'items' => [],
                'photo_count' => 0,
                'video_count' => 0
            ];
        }
        $s[$k]['items'][] = ['type' => 'photo', 'path' => $f, 'mtime' => filemtime($f), 'filename' => basename($f)];
        $s[$k]['photo_count']++;
    }
    
    foreach ($v as $f) {
        $b = basename($f);
        if (!preg_match($pat, $b, $m)) continue;
        $k = $m[1] . '_' . $m[2];
        if (!isset($s[$k])) {
            $s[$k] = [
                'ts' => $m[1], 
                'session' => $m[2], 
                'items' => [],
                'photo_count' => 0,
                'video_count' => 0
            ];
        }
        $s[$k]['items'][] = ['type' => 'video', 'path' => $f, 'mtime' => filemtime($f), 'filename' => basename($f)];
        $s[$k]['video_count']++;
    }
    
    // Sort items within each session by mtime
    foreach ($s as &$session) {
        usort($session['items'], function($a, $b) {
            return $a['mtime'] <=> $b['mtime'];
        });
    }
    
    return $s;
}

function format_date($timestamp_str) {
    $dt = DateTime::createFromFormat('Y-m-d_H-i-s', $timestamp_str);
    return $dt ? $dt->format('M j, Y • g:i A') : $timestamp_str;
}

function format_filesize($path) {
    $bytes = filesize($path);
    $units = ['B', 'KB', 'MB', 'GB'];
    for ($i = 0; $bytes > 1024 && $i < 3; $i++) {
        $bytes /= 1024;
    }
    return round($bytes, 1) . ' ' . $units[$i];
}

$sessions = build_sessions();
$key = $_GET['key'] ?? '';
$found = $sessions[$key] ?? null;
?>
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?php echo $found ? 'Session ' . h($found['session']) : 'Session Not Found'; ?> - Widowmont Drive Church</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Creepster&family=Nosifer&family=Butcherman&display=swap" rel="stylesheet">
</head>
<body>
    <header class="site-header session-header">
        <div class="container">
            <div class="header-nav">
                <a href="index.php" class="back-link">← Back to Gallery</a>
                <?php if ($found): ?>
                <div class="session-actions">
                    <button onclick="downloadAll()" class="download-all-btn">📥 Download All</button>
                </div>
                <?php endif; ?>
            </div>
            <?php if ($found): ?>
            <h1 class="session-title">
                <span class="bat">🦇</span>
                Session <?php echo h($found['session']); ?>
                <span class="bat">🦇</span>
            </h1>
            <div class="session-meta">
                <span class="session-date"><?php echo format_date($found['ts']); ?></span>
                <span class="session-stats">
                    <?php if ($found['photo_count'] > 0): ?>
                    <span>📸 <?php echo $found['photo_count']; ?> photos</span>
                    <?php endif; ?>
                    <?php if ($found['video_count'] > 0): ?>
                    <span>🎬 <?php echo $found['video_count']; ?> videos</span>
                    <?php endif; ?>
                </span>
            </div>
            <?php endif; ?>
        </div>
    </header>

    <main class="container">
        <?php if (!$found): ?>
        <div class="empty-state">
            <div class="empty-icon">💀</div>
            <h2>Session Not Found</h2>
            <p>This dark encounter has vanished into the void...</p>
            <a href="index.php" class="cta-btn">Return to Gallery</a>
        </div>
        <?php else: ?>
        <div class="media-grid">
            <?php foreach ($found['items'] as $idx => $it): ?>
            <div class="media-item" data-type="<?php echo $it['type']; ?>">
                <?php if ($it['type'] === 'photo'): ?>
                <div class="media-thumbnail" onclick="openLightbox('<?php echo h($it['path']); ?>', 'photo', <?php echo $idx; ?>)">
                    <img src="<?php echo h($it['path']); ?>" alt="Photo <?php echo $idx + 1; ?>" loading="lazy">
                    <div class="media-overlay">
                        <div class="media-icon">🔍</div>
                        <div class="media-label">View Photo</div>
                    </div>
                </div>
                <?php else: ?>
                <div class="media-thumbnail video-thumb" onclick="openLightbox('<?php echo h($it['path']); ?>', 'video', <?php echo $idx; ?>)">
                    <video muted preload="metadata">
                        <source src="<?php echo h($it['path']); ?>#t=0.5" type="video/mp4">
                    </video>
                    <div class="media-overlay">
                        <div class="media-icon">▶️</div>
                        <div class="media-label">Play Video</div>
                    </div>
                </div>
                <?php endif; ?>
                
                <div class="media-info">
                    <div class="media-details">
                        <span class="media-type"><?php echo strtoupper($it['type']); ?></span>
                        <span class="media-size"><?php echo format_filesize($it['path']); ?></span>
                    </div>
                    <a href="<?php echo h($it['path']); ?>" download="<?php echo h($it['filename']); ?>" class="download-btn">
                        📥 Download
                    </a>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>
    </main>

    <!-- Lightbox -->
    <div id="lightbox" class="lightbox" style="display: none;" onclick="closeLightbox()">
        <div class="lightbox-content" onclick="event.stopPropagation()">
            <button class="lightbox-close" onclick="closeLightbox()">×</button>
            <div class="lightbox-nav">
                <button class="nav-btn prev-btn" onclick="prevMedia()">‹</button>
                <button class="nav-btn next-btn" onclick="nextMedia()">›</button>
            </div>
            <div class="lightbox-body" id="lightbox-body">
                <!-- Content loaded dynamically -->
            </div>
            <div class="lightbox-info">
                <span id="lightbox-counter"></span>
                <a id="lightbox-download" class="lightbox-download-btn" download>📥 Download</a>
            </div>
        </div>
    </div>

    <footer class="site-footer">
        <div class="container">
            <p>🕯️ Widowmont Drive Church of the Unholy • Halloween <?php echo date('Y'); ?> 🕯️</p>
        </div>
    </footer>

    <script>
        const mediaItems = <?php echo json_encode($found ? $found['items'] : []); ?>;
        let currentIndex = 0;

        function openLightbox(path, type, index) {
            currentIndex = index;
            const lightbox = document.getElementById('lightbox');
            const body = document.getElementById('lightbox-body');
            const counter = document.getElementById('lightbox-counter');
            const download = document.getElementById('lightbox-download');
            
            body.innerHTML = '';
            
            if (type === 'photo') {
                const img = document.createElement('img');
                img.src = path;
                img.alt = 'Photo';
                body.appendChild(img);
            } else {
                const video = document.createElement('video');
                video.src = path;
                video.controls = true;
                video.autoplay = true;
                body.appendChild(video);
            }
            
            counter.textContent = `${index + 1} of ${mediaItems.length}`;
            download.href = path;
            download.download = mediaItems[index].filename;
            
            lightbox.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }

        function closeLightbox() {
            const lightbox = document.getElementById('lightbox');
            const body = document.getElementById('lightbox-body');
            
            // Pause any playing videos
            const videos = body.querySelectorAll('video');
            videos.forEach(video => video.pause());
            
            lightbox.style.display = 'none';
            document.body.style.overflow = '';
        }

        function prevMedia() {
            currentIndex = currentIndex > 0 ? currentIndex - 1 : mediaItems.length - 1;
            const item = mediaItems[currentIndex];
            openLightbox(item.path, item.type, currentIndex);
        }

        function nextMedia() {
            currentIndex = currentIndex < mediaItems.length - 1 ? currentIndex + 1 : 0;
            const item = mediaItems[currentIndex];
            openLightbox(item.path, item.type, currentIndex);
        }

        function downloadAll() {
            if (confirm('Download all photos and videos from this session?')) {
                mediaItems.forEach((item, idx) => {
                    setTimeout(() => {
                        const a = document.createElement('a');
                        a.href = item.path;
                        a.download = item.filename;
                        a.click();
                    }, idx * 500); // Stagger downloads
                });
            }
        }

        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            const lightbox = document.getElementById('lightbox');
            if (lightbox.style.display === 'flex') {
                if (e.key === 'Escape') {
                    closeLightbox();
                } else if (e.key === 'ArrowLeft') {
                    prevMedia();
                } else if (e.key === 'ArrowRight') {
                    nextMedia();
                }
            }
        });
    </script>
</body>
</html>
