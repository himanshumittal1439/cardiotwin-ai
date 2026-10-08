"""
Three.js WebGL 3D Heart Viewer Component for CardioTwin
=======================================================
Renders photorealistic textured 3D human heart with normal maps,
physiologically synchronized pulsatile beating animation, and orbit controls.
"""
import os
import streamlit as st

@st.cache_data
def get_gltf_json_data() -> str:
    """Reads and caches the self-contained base64 glTF model."""
    gltf_path = os.path.join(os.path.dirname(__file__), "..", "assets", "heart_3d", "heart_standalone.gltf")
    if os.path.exists(gltf_path):
        with open(gltf_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def render_photorealistic_heart_html(hr: float = 75.0, ef: float = 55.0, height: int = 370) -> str:
    """Generates the self-contained Three.js WebGL HTML string."""
    gltf_data = get_gltf_json_data()
    if not gltf_data:
        return "<div>3D Model file not found.</div>"

    beat_freq = hr / 60.0
    contraction_amp = max(0.04, min(0.18, (ef / 100.0) * 0.14))

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: linear-gradient(135deg, #090D16 0%, #111827 50%, #1F2937 100%);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            #canvas-container {{
                width: 100%;
                height: {height}px;
                position: relative;
            }}
            #controls-overlay {{
                position: absolute;
                top: 8px;
                left: 10px;
                background: rgba(15, 23, 42, 0.82);
                backdrop-filter: blur(8px);
                padding: 5px 12px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #F8FAFC;
                font-size: 11px;
                pointer-events: none;
                z-index: 10;
            }}
            #status-badge {{
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10B981;
                margin-right: 5px;
                box-shadow: 0 0 8px #10B981;
            }}
            #hint {{
                position: absolute;
                bottom: 8px;
                right: 12px;
                color: #94A3B8;
                font-size: 10px;
                pointer-events: none;
                background: rgba(15, 23, 42, 0.6);
                padding: 3px 8px;
                border-radius: 4px;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <div id="controls-overlay">
                <span id="status-badge"></span>
                <strong>Photorealistic 3D Heart Twin</strong> | {int(hr)} bpm | EF: {ef}%
            </div>
            <div id="hint">🖱️ Drag to rotate 360° • Scroll to zoom • Right-click to pan</div>
        </div>

        <script>
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth || window.innerWidth;
            const height = {height};

            const scene = new THREE.Scene();

            const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            camera.position.set(0, 0, 4.4);

            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(width, height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.35;
            renderer.outputEncoding = THREE.sRGBEncoding;
            container.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.8;
            controls.minDistance = 1.8;
            controls.maxDistance = 7.5;

            // Lighting setup for photorealistic tissue & specular reflection
            const ambientLight = new THREE.AmbientLight(0xffffff, 1.3);
            scene.add(ambientLight);

            const mainLight = new THREE.DirectionalLight(0xfff7ed, 2.4);
            mainLight.position.set(6, 8, 7);
            scene.add(mainLight);

            const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.5);
            rimLight.position.set(-6, -2, -4);
            scene.add(rimLight);

            const fillLight = new THREE.DirectionalLight(0xef4444, 0.9);
            fillLight.position.set(0, -6, 5);
            scene.add(fillLight);

            let heartModel = null;
            const beatFreq = {beat_freq};
            const contractionAmp = {contraction_amp};

            const gltfData = {gltf_data};

            const loader = new THREE.GLTFLoader();
            loader.parse(JSON.stringify(gltfData), '', function (gltf) {{
                heartModel = gltf.scene;

                // Center bounding box
                const box = new THREE.Box3().setFromObject(heartModel);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());

                const maxDim = Math.max(size.x, size.y, size.z);
                const scale = 2.25 / maxDim;
                heartModel.scale.set(scale, scale, scale);
                heartModel.position.sub(center.multiplyScalar(scale));

                // Natural anatomical tilt
                heartModel.rotation.x = 0.15;
                heartModel.rotation.y = -0.35;

                scene.add(heartModel);
            }}, undefined, function (error) {{
                console.error("Error loading glTF:", error);
            }});

            const clock = new THREE.Clock();

            function animate() {{
                requestAnimationFrame(animate);
                controls.update();

                if (heartModel) {{
                    const elapsed = clock.getElapsedTime();
                    // Physiological Wiggers ventricular contraction pulse
                    const phase = (elapsed * beatFreq) % 1.0;
                    let pulse = 0;
                    if (phase < 0.35) {{
                        pulse = Math.sin((phase / 0.35) * Math.PI);
                    }}
                    
                    const s = 1.0 - contractionAmp * pulse;
                    heartModel.scale.set(s, s * 1.02, s);
                }}

                renderer.render(scene, camera);
            }}

            animate();

            window.addEventListener('resize', () => {{
                const newWidth = container.clientWidth;
                camera.aspect = newWidth / height;
                camera.updateProjectionMatrix();
                renderer.setSize(newWidth, height);
            }});
        </script>
    </body>
    </html>
    """
