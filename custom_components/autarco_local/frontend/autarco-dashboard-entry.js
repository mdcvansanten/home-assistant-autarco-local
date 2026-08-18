// Autarco Local v0.6.6 frontend entry point.
// Start with the v0.6.5 collision-safe bootstrap, then layer the v0.6.6
// dashboard/diagnostics/data-quality/scenario, single-setting and UI-state extensions.
// Stability, transaction UX, unlock guard and the final hardware safety gate are
// intentionally last so safety state wins over earlier hot-loaded UI patches.
import "./autarco-dashboard-bootstrap.js?v=0.6.5.2";
import "./autarco-dashboard-v066-patch.js?v=0.6.6.2";
import "./autarco-dashboard-v066-diagnostics.js?v=0.6.6";
import "./autarco-dashboard-v066-data-quality.js?v=0.6.6";
import "./autarco-dashboard-v066-write.js?v=0.6.6";
import "./autarco-dashboard-v066-ui-state.js?v=0.6.6.5";
import "./autarco-dashboard-v066-stability.js?v=0.6.6.5";
import "./autarco-dashboard-v066-transaction-ux.js?v=0.6.6.8";
import "./autarco-dashboard-v066-unlock-guard.js?v=0.6.6.7";
import "./autarco-dashboard-v066-safety.js?v=0.6.6.9";
