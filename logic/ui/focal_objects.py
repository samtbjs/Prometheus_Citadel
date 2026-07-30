"""
MILESTONE 4: one entry per anomaly that has a live 3D scene. Each entry
supplies the two pieces of JS that scenes/anomaly_acene.html's generic
template plugs into itself (see that file's header comment) -- everything
else (camera, lights, fog, the resolved/thin/wrong reaction logic) is
shared and lives only in the template, not repeated here.

focal_setup_js: runs ONCE on scene load. Must build this anomaly's shape(s)
    into `focalGroup` (a THREE.Group already created by the template) and
    push every MeshStandardMaterial that should glow on reaction into the
    `reactiveMeshes` array (also already created by the template).
idle_tick_js: runs every animation frame (~60/sec) for this anomaly's own
    idle motion. `reactionState.speed` is available to speed up/slow down
    with the calm/agitated reaction states, same as vacuum_box already did.
accent_hex: this anomaly's chapter accent, as a "0xRRGGBB" JS literal
    string, pulled from ui/design_tokens.py by scene_viewer.py.
fallback_text: shown by the 2D fallback if the 3D assets can't be read.
"""

FOCAL_OBJECT_CONFIG = {
    # ---- Mechanics (cyan) -- unchanged from the original scene ----------
    "vacuum_box": {
        "focal_setup_js": """
        const geometry = new THREE.BoxGeometry(1.4, 1.4, 1.4);
        const material = new THREE.MeshStandardMaterial({
          color: ACCENT_HEX, metalness: 0.3, roughness: 0.4,
          emissive: 0x000000, emissiveIntensity: 1,
        });
        const box = new THREE.Mesh(geometry, material);
        focalGroup.add(box);
        reactiveMeshes.push(material);
        const idleBaseY = box.position.y;
        """,
        "idle_tick_js": """
        box.rotation.y += 0.0035 * reactionState.speed;
        box.rotation.x += 0.0015 * reactionState.speed;
        box.position.y = idleBaseY + Math.sin(Date.now() * 0.0006) * 0.12;
        """,
        "fallback_text": "A box floats motionless in a vacuum chamber, with nothing touching it.",
        "accent_token": "CHAPTER_1_ACCENT",
    },

    # ---- Mechanics (cyan) -- constant slow sinking drift -----------------
    "sinking_stone": {
        "focal_setup_js": """
        const geometry = new THREE.IcosahedronGeometry(0.9, 0);
        const material = new THREE.MeshStandardMaterial({
          color: ACCENT_HEX, metalness: 0.1, roughness: 0.85, flatShading: true,
          emissive: 0x000000, emissiveIntensity: 1,
        });
        const stone = new THREE.Mesh(geometry, material);
        focalGroup.add(stone);
        reactiveMeshes.push(material);
        const idleTopY = 1.6, idleBottomY = -1.6;
        stone.position.y = idleTopY;
        """,
        "idle_tick_js": """
        stone.position.y -= 0.006 * reactionState.speed;
        if (stone.position.y < idleBottomY) stone.position.y = idleTopY;
        stone.rotation.x += 0.004 * reactionState.speed;
        stone.rotation.z += 0.002 * reactionState.speed;
        """,
        "fallback_text": "A stone released underwater sinks at a constant speed and never gets any faster.",
        "accent_token": "CHAPTER_1_ACCENT",
    },

    # ---- Thermal (amber) -- two contrasting objects + heat shimmer -------
    "hot_cold_chairs": {
        "focal_setup_js": """
        const hotGeo = new THREE.BoxGeometry(1, 1.4, 1);
        const hotMat = new THREE.MeshStandardMaterial({
          color: ACCENT_HEX, metalness: 0.2, roughness: 0.5,
          emissive: 0xff6a00, emissiveIntensity: 0.55,
        });
        const hotChair = new THREE.Mesh(hotGeo, hotMat);
        hotChair.position.x = -1.1;
        focalGroup.add(hotChair);
        reactiveMeshes.push(hotMat);

        const coldGeo = new THREE.BoxGeometry(1, 1.4, 1);
        const coldMat = new THREE.MeshStandardMaterial({
          color: 0x33475a, metalness: 0.4, roughness: 0.3,
          emissive: 0x000000, emissiveIntensity: 0.6,
        });
        const coldChair = new THREE.Mesh(coldGeo, coldMat);
        coldChair.position.x = 1.1;
        focalGroup.add(coldChair);
        reactiveMeshes.push(coldMat);

        // Heat-shimmer particles drifting up off the hot chair only --
        // this chapter's first visual-identity moment.
        const particleGeo = new THREE.SphereGeometry(0.035, 6, 6);
        const particleMat = new THREE.MeshBasicMaterial({ color: 0xffb066, transparent: true, opacity: 0.55 });
        const particles = [];
        for (let i = 0; i < 14; i++) {
          const p = new THREE.Mesh(particleGeo, particleMat);
          p.userData.baseX = hotChair.position.x + (Math.random() - 0.5) * 0.8;
          p.position.set(p.userData.baseX, Math.random() * 1.6 - 0.7, (Math.random() - 0.5) * 0.6);
          p.userData.speed = 0.004 + Math.random() * 0.006;
          focalGroup.add(p);
          particles.push(p);
        }
        """,
        "idle_tick_js": """
        hotChair.rotation.y = Math.sin(Date.now() * 0.0004) * 0.06;
        coldChair.rotation.y = Math.sin(Date.now() * 0.0004 + Math.PI) * 0.03;
        particles.forEach((p) => {
          p.position.y += p.userData.speed * reactionState.speed;
          p.position.x = p.userData.baseX + Math.sin(Date.now() * 0.002 + p.position.y * 3) * 0.05;
          if (p.position.y > 1.0) p.position.y = -0.7;
        });
        """,
        "fallback_text": "A metal chair and a wooden chair sit in the same room, but the metal one feels colder to the touch.",
        "accent_token": "CHAPTER_2_ACCENT",
    },

    # ---- Quantum (violet) -- orbiting sphere + a visible clock pulse -----
    "gps_clock_drift": {
        "focal_setup_js": """
        const centerGeo = new THREE.SphereGeometry(0.28, 16, 16);
        const centerMat = new THREE.MeshStandardMaterial({
          color: ACCENT_HEX, metalness: 0.4, roughness: 0.3,
          emissive: 0x000000, emissiveIntensity: 1,
        });
        const centerSphere = new THREE.Mesh(centerGeo, centerMat);
        focalGroup.add(centerSphere);
        reactiveMeshes.push(centerMat);

        // Clock-pulse ring: expands and fades on a steady beat.
        const pulseGeo = new THREE.RingGeometry(0.32, 0.36, 32);
        const pulseMat = new THREE.MeshBasicMaterial({ color: ACCENT_HEX, transparent: true, opacity: 0.5, side: THREE.DoubleSide });
        const pulseRing = new THREE.Mesh(pulseGeo, pulseMat);
        pulseRing.rotation.x = Math.PI / 2;
        focalGroup.add(pulseRing);

        const orbitGeo = new THREE.SphereGeometry(0.14, 12, 12);
        const orbitMat = new THREE.MeshStandardMaterial({
          color: 0xd8c6ff, metalness: 0.3, roughness: 0.4,
          emissive: 0x000000, emissiveIntensity: 1,
        });
        const orbiter = new THREE.Mesh(orbitGeo, orbitMat);
        focalGroup.add(orbiter);
        reactiveMeshes.push(orbitMat);

        const orbitRadius = 1.5;
        let orbitAngle = 0;
        let pulseClock = 0;
        """,
        "idle_tick_js": """
        orbitAngle += 0.012 * reactionState.speed;
        orbiter.position.set(
          Math.cos(orbitAngle) * orbitRadius,
          Math.sin(orbitAngle * 1.3) * 0.25,
          Math.sin(orbitAngle) * orbitRadius
        );
        centerSphere.rotation.y += 0.01 * reactionState.speed;
        pulseClock = (pulseClock + 0.015 * reactionState.speed) % 1.0;
        const pulseScale = 1 + pulseClock * 2.2;
        pulseRing.scale.set(pulseScale, pulseScale, pulseScale);
        pulseRing.material.opacity = 0.5 * (1 - pulseClock);
        """,
        "fallback_text": "A GPS satellite's onboard clock runs faster than an identical clock on the ground, even though nothing on the satellite is broken.",
        "accent_token": "CHAPTER_3_ACCENT",
    },
}
