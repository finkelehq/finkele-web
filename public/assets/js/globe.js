// Climate Globe Visualization Module
// Separate file to keep globe logic independent

(function() {
    'use strict';
    
    // Check if Three.js is available
    function initClimateGlobe() {
        const container = document.getElementById('climate-globe');
        if (!container) {
            console.warn('Climate globe container not found');
            return;
        }
        
        // If Three.js is not loaded, create CSS fallback
        if (typeof THREE === 'undefined') {
            console.warn('Three.js not loaded, using CSS fallback');
            createCSSGlobe(container);
            return;
        }
        
        // Three.js Globe
        const width = container.offsetWidth || 500;
        const height = container.offsetHeight || 500;
        
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.z = 2.5;
        
        const renderer = new THREE.WebGLRenderer({ 
            alpha: true, 
            antialias: true 
        });
        renderer.setSize(width, height);
        renderer.setClearColor(0x000000, 0);
        container.appendChild(renderer.domElement);
        
        // Create globe
        const globeGeometry = new THREE.SphereGeometry(1, 32, 32);
        const globeMaterial = new THREE.MeshPhongMaterial({
            color: 0x22c55e,
            emissive: 0x22c55e,
            emissiveIntensity: 0.1,
            shininess: 100,
            specular: 0x00ff88
        });
        
        const globe = new THREE.Mesh(globeGeometry, globeMaterial);
        scene.add(globe);
        
        // Add wireframe for tech look
        const wireframeGeometry = new THREE.SphereGeometry(1.01, 16, 16);
        const wireframeMaterial = new THREE.MeshBasicMaterial({
            color: 0x00ff88,
            wireframe: true,
            transparent: true,
            opacity: 0.15
        });
        const wireframe = new THREE.Mesh(wireframeGeometry, wireframeMaterial);
        scene.add(wireframe);
        
        // Add climate data points
        const createDataPoints = () => {
            const pointsGeometry = new THREE.BufferGeometry();
            const pointsCount = 30;
            const positions = new Float32Array(pointsCount * 3);
            const colors = new Float32Array(pointsCount * 3);
            
            for (let i = 0; i < pointsCount; i++) {
                // Random points on sphere surface
                const theta = Math.random() * Math.PI * 2;
                const phi = Math.acos(Math.random() * 2 - 1);
                const radius = 1.05;
                
                positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
                positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
                positions[i * 3 + 2] = radius * Math.cos(phi);
                
                // Color variation (yellow to red for heat map effect)
                colors[i * 3] = 1.0;
                colors[i * 3 + 1] = Math.random() * 0.5 + 0.5;
                colors[i * 3 + 2] = 0.0;
            }
            
            pointsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            pointsGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            
            const pointsMaterial = new THREE.PointsMaterial({
                size: 0.03,
                vertexColors: true,
                transparent: true,
                opacity: 0.8,
                blending: THREE.AdditiveBlending
            });
            
            return new THREE.Points(pointsGeometry, pointsMaterial);
        };
        
        const dataPoints = createDataPoints();
        scene.add(dataPoints);
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(1, 1, 1);
        scene.add(directionalLight);
        
        const pointLight = new THREE.PointLight(0x00ff88, 0.5);
        pointLight.position.set(-2, 2, 2);
        scene.add(pointLight);
        
        // Animation variables
        let time = 0;
        const clock = new THREE.Clock();
        
        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
            
            const delta = clock.getDelta();
            time += delta;
            
            // Rotate globe and wireframe
            globe.rotation.y += 0.003;
            wireframe.rotation.y += 0.003;
            dataPoints.rotation.y += 0.003;
            
            // Pulse effect
            const scale = 1 + Math.sin(time * 2) * 0.02;
            globe.scale.set(scale, scale, scale);
            
            // Animate data points
            dataPoints.material.opacity = 0.5 + Math.sin(time * 3) * 0.3;
            
            renderer.render(scene, camera);
        }
        
        animate();
        
        // Handle resize
        function handleResize() {
            const newWidth = container.offsetWidth;
            const newHeight = container.offsetHeight;
            
            camera.aspect = newWidth / newHeight;
            camera.updateProjectionMatrix();
            
            renderer.setSize(newWidth, newHeight);
        }
        
        window.addEventListener('resize', handleResize);
        
        // Store reference for cleanup if needed
        container._globeRenderer = renderer;
        container._globeAnimation = animate;
    }
    
    // CSS Fallback Globe
    function createCSSGlobe(container) {
        container.innerHTML = `
            <div style="
                width: 100%;
                height: 100%;
                background: radial-gradient(circle at 30% 30%, #4ade80, #22c55e, #16a34a);
                border-radius: 50%;
                box-shadow: 
                    0 0 60px rgba(34, 197, 94, 0.5),
                    inset -20px -20px 40px rgba(0, 0, 0, 0.3),
                    inset 20px 20px 40px rgba(255, 255, 255, 0.1);
                animation: cssGlobeRotate 20s linear infinite;
                position: relative;
                overflow: hidden;
            ">
                <div style="
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    background: repeating-linear-gradient(
                        90deg,
                        transparent,
                        transparent 10px,
                        rgba(255, 255, 255, 0.03) 10px,
                        rgba(255, 255, 255, 0.03) 20px
                    );
                    animation: cssGlobeScan 3s linear infinite;
                "></div>
            </div>
            <style>
                @keyframes cssGlobeRotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                @keyframes cssGlobeScan {
                    from { transform: translateX(-20px); }
                    to { transform: translateX(20px); }
                }
            </style>
        `;
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initClimateGlobe);
    } else {
        initClimateGlobe();
    }
    
    // Export for external use if needed
    window.initClimateGlobe = initClimateGlobe;
})();