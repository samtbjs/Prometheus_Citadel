"""
MILESTONE 7: reduced-motion + mobile-safe camera framing, shared across
every scene. ONE JS snippet (MOTION_JS) is inlined ahead of each scene's
own <script> (same inlining pattern ui/scene_viewer.py already uses for
static/vendor/three.min.js + gsap.min.js), so no scene re-implements the
matchMedia check, the "jump a timeline to its end" logic, or its own
camera/aspect math with different numbers.

What a scene's own <script> gets, already defined, before it runs:
  PM_REDUCED_MOTION  (bool) -- true if the OS/browser prefers reduced
      motion. Read once; matchMedia doesn't need live-updating here
      since each scene is a fresh iframe on every Streamlit rerun.
  pmSkip(tl)         -- wrap any GSAP timeline: if PM_REDUCED_MOTION,
      jumps it straight to its end state with no visual playback
      (suppressing its callbacks) and returns it either way, so
      `pmSkip(gsap.timeline()....)` drops in around any existing
      timeline chain without changing its tweens/timing when motion
      IS allowed.
  pmFitCamera(camera, w, h, opts) -- call on initial setup AND inside
      every resize handler instead of the old two-line
      "camera.aspect = w/h; camera.updateProjectionMatrix()". Keeps
      camera.fov equal to opts.baseFov (or the camera's current fov if
      omitted) at normal-ish aspect ratios, and widens it as the
      viewport gets narrower/taller than opts.minAspect so a
      phone-width iframe doesn't crop the sides of the scene -- same
      composition, just a wider vertical FOV to compensate for the
      narrower horizontal one. Caps the widened fov at opts.maxFov
      (default 85) so it never goes fisheye-extreme.
"""

MOTION_JS = """
var PM_REDUCED_MOTION = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

function pmSkip(tl) {
  if (PM_REDUCED_MOTION && tl && typeof tl.progress === 'function') {
    tl.progress(1, true);
  }
  return tl;
}

function pmFitCamera(camera, w, h, opts) {
  opts = opts || {};
  var baseFov = opts.baseFov || camera.fov;
  var minAspect = opts.minAspect || 0.62;
  var maxFov = opts.maxFov || 85;
  var aspect = w / Math.max(h, 1);
  camera.aspect = aspect;
  camera.fov = aspect < minAspect ? Math.min(baseFov * (minAspect / aspect), maxFov) : baseFov;
  camera.updateProjectionMatrix();
}
"""
