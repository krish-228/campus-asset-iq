/**
 * CampusAssetIQ - Universal Table Drag-to-Scroll Engine
 * Enables smooth click-and-drag horizontal scrolling (right-to-left and left-to-right)
 * with mouse cursor across all tables.
 */
(function () {
    // Inject styles for grab/grabbing cursor and scrollbar enhancement
    const style = document.createElement('style');
    style.id = 'table-drag-scroll-styles';
    style.textContent = `
        .table-cursor-scrollable {
            cursor: grab !important;
            scrollbar-width: thin;
        }
        .table-cursor-scrollable:active,
        .table-cursor-scrollable.is-mouse-dragging {
            cursor: grabbing !important;
            user-select: none !important;
            -webkit-user-select: none !important;
        }
        .table-cursor-scrollable.is-mouse-dragging * {
            cursor: grabbing !important;
            user-select: none !important;
            -webkit-user-select: none !important;
        }
        .table-cursor-scrollable::-webkit-scrollbar {
            height: 8px;
        }
        .table-cursor-scrollable::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 4px;
        }
        .table-cursor-scrollable::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
        }
        .table-cursor-scrollable::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
    `;
    if (!document.getElementById('table-drag-scroll-styles')) {
        document.head.appendChild(style);
    }

    function initContainerDragScroll(container) {
        if (!container || container.dataset.dragScrollInitialized === 'true') return;
        container.dataset.dragScrollInitialized = 'true';

        let isDown = false;
        let startX = 0;
        let scrollLeft = 0;
        let isDragging = false;
        let dragDistance = 0;
        let velX = 0;
        let lastX = 0;
        let lastTime = 0;
        let momentumID = null;

        container.classList.add('table-cursor-scrollable');

        // Mouse Down: start drag tracking
        container.addEventListener('mousedown', (e) => {
            // Ignore right click
            if (e.button !== 0) return;
            // Allow interactions if clicking interactive form controls directly without moving
            const isInteractive = !!e.target.closest('button, a, input, select, textarea, [role="button"], label');
            
            isDown = true;
            isDragging = false;
            dragDistance = 0;
            startX = e.pageX - container.offsetLeft;
            scrollLeft = container.scrollLeft;
            lastX = e.pageX;
            lastTime = performance.now();
            velX = 0;

            if (momentumID) {
                cancelAnimationFrame(momentumID);
                momentumID = null;
            }

            // Only set grabbing immediately if not directly on an interactive control
            if (!isInteractive) {
                container.classList.add('is-mouse-dragging');
            }
        });

        // Mouse Move: perform scroll
        window.addEventListener('mousemove', (e) => {
            if (!isDown) return;

            const currentX = e.pageX - container.offsetLeft;
            const diffX = currentX - startX;
            dragDistance += Math.abs(e.pageX - lastX);

            // Calculate velocity for momentum on release
            const now = performance.now();
            const dt = now - lastTime;
            if (dt > 0) {
                velX = (e.pageX - lastX) / dt;
            }
            lastX = e.pageX;
            lastTime = now;

            // Threshold of 4px before activating drag state
            if (dragDistance > 4) {
                if (!isDragging) {
                    isDragging = true;
                    container.classList.add('is-mouse-dragging');
                }
                e.preventDefault();
                // 1.35x speed multiplier for smooth responsiveness
                container.scrollLeft = scrollLeft - (diffX * 1.35);
            }
        }, { passive: false });

        // End Drag function
        function endDrag() {
            if (!isDown) return;
            isDown = false;
            container.classList.remove('is-mouse-dragging');

            // Apply momentum glide if dragged with velocity
            if (isDragging && Math.abs(velX) > 0.2) {
                let currentVel = velX * 16; // approximate frame velocity
                function stepMomentum() {
                    if (Math.abs(currentVel) > 0.5) {
                        container.scrollLeft -= currentVel;
                        currentVel *= 0.92; // friction
                        momentumID = requestAnimationFrame(stepMomentum);
                    } else {
                        momentumID = null;
                    }
                }
                momentumID = requestAnimationFrame(stepMomentum);
            }

            // Reset isDragging after click events pass
            setTimeout(() => {
                isDragging = false;
            }, 60);
        }

        window.addEventListener('mouseup', endDrag);

        // Suppress click events on child elements if the mouse was dragged
        container.addEventListener('click', (e) => {
            if (isDragging || dragDistance > 6) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
            }
        }, true);

    }

    // Global scroll helper for Left / Right buttons
    window.scrollTableHorizontally = function (tableOrContainerId, amount) {
        let el = document.getElementById(tableOrContainerId);
        if (!el) return;
        let container = el.classList.contains('overflow-x-auto') ? el : el.closest('.overflow-x-auto');
        if (!container) container = el.parentElement;
        if (container) {
            container.scrollBy({
                left: amount,
                behavior: 'smooth'
            });
        }
    };

    // Scan DOM and attach to all table containers
    function scanAndAttachTables() {
        const containers = document.querySelectorAll('.overflow-x-auto, [data-table-scroll]');
        containers.forEach(c => {
            if (c.querySelector('table') || c.classList.contains('table-scroll-container')) {
                initContainerDragScroll(c);
            }
        });

        // Also check any standalone table parent
        document.querySelectorAll('table').forEach(tbl => {
            const parent = tbl.parentElement;
            if (parent && getComputedStyle(parent).overflowX === 'auto') {
                initContainerDragScroll(parent);
            }
        });
    }

    // Auto-run on DOM ready and dynamic changes
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', scanAndAttachTables);
    } else {
        scanAndAttachTables();
    }

    // Observe dynamic DOM changes (e.g. AJAX table updates)
    if (typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(() => {
            scanAndAttachTables();
        });
        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true });
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                observer.observe(document.body, { childList: true, subtree: true });
            });
        }
    }

    // Expose utility globally
    window.initTableDragScroll = scanAndAttachTables;
})();
