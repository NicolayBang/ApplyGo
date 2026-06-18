import { ClipboardCheck, FileText, Gauge, Inbox, ListChecks, Route } from "lucide-react";

const navItems = [
  { href: "#dashboard", label: "Dashboard", icon: Gauge },
  { href: "#applications", label: "Applications", icon: Inbox },
  { href: "#manual-intake", label: "Manual intake", icon: FileText },
  { href: "#review", label: "Review", icon: ClipboardCheck },
  { href: "#packet", label: "Packet", icon: ListChecks },
  { href: "#timeline", label: "Timeline", icon: Route },
];

export function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Dashboard navigation">
      <div className="sidebar-brand">
        <span className="brand-mark" aria-hidden="true" />
        <span>ApplyGo</span>
      </div>
      <nav className="sidebar-nav" aria-label="Primary">
        {navItems.map(({ href, label, icon: Icon }, index) => (
          <a className={index === 0 ? "active" : ""} href={href} key={href}>
            <Icon aria-hidden="true" size={16} />
            <span>{label}</span>
          </a>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span>Dry-run safe</span>
        <strong>No external side effects</strong>
      </div>
    </aside>
  );
}
