// Autarco Local v0.6.6 frontend entry point.
// The stable v0.6.5 panel is loaded first; v0.6.6 layers only the tested fixes
// and extensions on top so rollback remains straightforward during hardware testing.
import "./autarco-dashboard-panel.js?v=0.6.5.1";
import "./autarco-dashboard-v066-patch.js?v=0.6.6";
import "./autarco-dashboard-v066-write.js?v=0.6.6";
