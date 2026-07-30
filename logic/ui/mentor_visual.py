"""
MILESTONE 5 (Part A): ARBITER's rotating core -- ONE reusable visual,
built from primitives only, using the SAME config-dict + shared-template
pattern as ui/focal_objects.py (see that file's header comment). The
shared templates are scenes/mentor_core.html (standalone use) and
scenes/debrief.html (embedded in the Debrief scene) -- both read
core_setup_js/core_idle_js from this same dict, so the visual itself is
defined exactly once.
"""

MENTOR_CORE_CONFIG = {
    "arbiter": {
        "core_setup_js": """
        const geometry = new THREE.IcosahedronGeometry(1.0, 0);
        const material = new THREE.MeshStandardMaterial({
          color: ACCENT_HEX, metalness: 0.35, roughness: 0.35, flatShading: true,
          emissive: ACCENT_HEX, emissiveIntensity: 0.25,
        });
        const core = new THREE.Mesh(geometry, material);
        scene.add(core);
        const wireGeo = new THREE.IcosahedronGeometry(1.35, 0);
        const wireMat = new THREE.MeshBasicMaterial({ color: ACCENT_HEX, wireframe: true, transparent: true, opacity: 0.35 });
        const wireShell = new THREE.Mesh(wireGeo, wireMat);
        scene.add(wireShell);
        """,
        "core_idle_js": """
        core.rotation.y += 0.006;
        core.rotation.x += 0.0025;
        wireShell.rotation.y -= 0.0035;
        wireShell.rotation.x += 0.0015;
        """,
    },
}
