import AppKit
import Foundation

private let cliPath = "/usr/local/bin/devfix-tunnel"
private let chromeLauncherPath = "/usr/local/bin/devfix-tunnel-chrome"
private let torCheckURL = "https://check.torproject.org/"

private struct TunnelStatus {
    var state = "UNKNOWN"
    var mode = "NONE"
    var session = ""
    var socks = ""
    var transport = ""
    var service = ""
    var health = ""
    var guardian = ""

    var isConnected: Bool { state == "CONNECTED" }
    var isBusy: Bool { ["STARTING", "BOOTSTRAPPING", "VALIDATING"].contains(state) }
    var isHealthySystemProxy: Bool { isConnected && mode == "SYSTEM_PROXY" && health == "OK" && !guardian.contains("DEGRADED") }

    var connectedSince: Date? {
        guard let first = session.split(separator: "-").first,
              let epoch = TimeInterval(first) else { return nil }
        return Date(timeIntervalSince1970: epoch)
    }
}

private enum PendingAction {
    case connectSafari
    case disconnect
    case repair
}

private final class CommandRunner {
    static func run(_ executable: String, _ arguments: [String], completion: @escaping (Int32, String) -> Void) {
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            let pipe = Pipe()
            process.executableURL = URL(fileURLWithPath: executable)
            process.arguments = arguments
            process.standardOutput = pipe
            process.standardError = pipe

            do {
                try process.run()
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                process.waitUntilExit()
                let text = String(data: data, encoding: .utf8) ?? ""
                DispatchQueue.main.async { completion(process.terminationStatus, text) }
            } catch {
                DispatchQueue.main.async { completion(127, error.localizedDescription) }
            }
        }
    }

    static func runSync(_ executable: String, _ arguments: [String]) -> (Int32, String) {
        let process = Process()
        let pipe = Pipe()
        process.executableURL = URL(fileURLWithPath: executable)
        process.arguments = arguments
        process.standardOutput = pipe
        process.standardError = pipe
        do {
            try process.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            return (process.terminationStatus, String(data: data, encoding: .utf8) ?? "")
        } catch {
            return (127, error.localizedDescription)
        }
    }
}

private final class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private let menu = NSMenu()

    private let stateItem = NSMenuItem(title: "State: checking…", action: nil, keyEquivalent: "")
    private let modeItem = NSMenuItem(title: "Mode: —", action: nil, keyEquivalent: "")
    private let routeItem = NSMenuItem(title: "Transport: —", action: nil, keyEquivalent: "")
    private let elapsedItem = NSMenuItem(title: "Connected: —", action: nil, keyEquivalent: "")
    private let exitItem = NSMenuItem(title: "Exit: —", action: nil, keyEquivalent: "")

    private var connectSafariItem: NSMenuItem!
    private var openSafariItem: NSMenuItem!
    private var disconnectItem: NSMenuItem!
    private var refreshExitItem: NSMenuItem!
    private var legacyChromeItem: NSMenuItem!

    private var refreshTimer: Timer?
    private var elapsedTimer: Timer?
    private var currentStatus = TunnelStatus()
    private var pendingAction: PendingAction?
    private var pendingSince: Date?
    private var cachedExit = "—"
    private var exitRefreshInFlight = false
    private var lastExitRefresh = Date.distantPast
    private var lastConnectedSession = ""

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        configureStatusItem()
        configureMenu()
        refreshStatus()

        refreshTimer = Timer.scheduledTimer(withTimeInterval: 1.5, repeats: true) { [weak self] _ in
            self?.refreshStatus()
        }
        elapsedTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.updateElapsed()
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        refreshTimer?.invalidate()
        elapsedTimer?.invalidate()
    }

    private func configureStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.menu = menu
        updateStatusIcon(for: currentStatus)
    }

    private func configureMenu() {
        for item in [stateItem, modeItem, routeItem, elapsedItem, exitItem] {
            item.isEnabled = false
            menu.addItem(item)
        }
        menu.addItem(.separator())

        connectSafariItem = NSMenuItem(title: "Connect Safari…", action: #selector(connectSafari), keyEquivalent: "")
        connectSafariItem.target = self
        menu.addItem(connectSafariItem)

        openSafariItem = NSMenuItem(title: "Open Safari", action: #selector(openSafariAction), keyEquivalent: "")
        openSafariItem.target = self
        menu.addItem(openSafariItem)

        disconnectItem = NSMenuItem(title: "Disconnect", action: #selector(disconnect), keyEquivalent: "")
        disconnectItem.target = self
        menu.addItem(disconnectItem)

        menu.addItem(.separator())

        refreshExitItem = NSMenuItem(title: "Refresh Exit IP / Country", action: #selector(refreshExitAction), keyEquivalent: "")
        refreshExitItem.target = self
        menu.addItem(refreshExitItem)

        let openCheckItem = NSMenuItem(title: "Open Tor Check in Safari", action: #selector(openTorCheck), keyEquivalent: "")
        openCheckItem.target = self
        menu.addItem(openCheckItem)

        let advancedItem = NSMenuItem(title: "Advanced", action: nil, keyEquivalent: "")
        let advancedMenu = NSMenu(title: "Advanced")

        let copySocksItem = NSMenuItem(title: "Copy SOCKS Address", action: #selector(copySocks), keyEquivalent: "")
        copySocksItem.target = self
        advancedMenu.addItem(copySocksItem)

        legacyChromeItem = NSMenuItem(title: "Legacy: Open Selective Chrome", action: #selector(openSelectiveChrome), keyEquivalent: "")
        legacyChromeItem.target = self
        advancedMenu.addItem(legacyChromeItem)

        let repairItem = NSMenuItem(title: "Repair…", action: #selector(repair), keyEquivalent: "")
        repairItem.target = self
        advancedMenu.addItem(repairItem)

        let refreshItem = NSMenuItem(title: "Refresh Status", action: #selector(refreshStatusAction), keyEquivalent: "r")
        refreshItem.target = self
        advancedMenu.addItem(refreshItem)

        advancedItem.submenu = advancedMenu
        menu.addItem(advancedItem)

        menu.addItem(.separator())

        let noteItem = NSMenuItem(title: "Safari Mode uses macOS System Proxy", action: nil, keyEquivalent: "")
        noteItem.isEnabled = false
        menu.addItem(noteItem)

        let quitItem = NSMenuItem(title: "Quit DevFix Tunnel UI", action: #selector(quit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)
    }

    private func parseStatus(_ text: String) -> TunnelStatus {
        var result = TunnelStatus()
        for rawLine in text.split(separator: "\n", omittingEmptySubsequences: false) {
            let line = String(rawLine)
            guard let colon = line.firstIndex(of: ":") else { continue }
            let key = String(line[..<colon]).trimmingCharacters(in: .whitespaces)
            let value = String(line[line.index(after: colon)...]).trimmingCharacters(in: .whitespaces)
            switch key {
            case "State": result.state = value
            case "Mode": result.mode = value
            case "Session": result.session = value
            case "SOCKS": result.socks = value
            case "Transport": result.transport = value
            case "System Proxy service": result.service = value
            case "Health": result.health = value
            case "Guardian": result.guardian = value
            default: break
            }
        }
        return result
    }

    private func refreshStatus() {
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let (code, output) = CommandRunner.runSync(cliPath, ["status"])
            let parsed = self?.parseStatus(output) ?? TunnelStatus()
            DispatchQueue.main.async {
                guard let self = self else { return }
                let previous = self.currentStatus
                if code == 127 {
                    self.currentStatus = TunnelStatus(state: "NOT_INSTALLED")
                } else {
                    self.currentStatus = parsed
                }
                self.handlePendingAction(previous: previous, current: self.currentStatus)
                self.renderStatus()
                self.maybeRefreshExit()
            }
        }
    }

    private func handlePendingAction(previous: TunnelStatus, current: TunnelStatus) {
        guard let action = pendingAction else { return }

        switch action {
        case .connectSafari:
            if current.isHealthySystemProxy {
                pendingAction = nil
                pendingSince = nil
                if current.session != lastConnectedSession {
                    lastConnectedSession = current.session
                    cachedExit = "checking…"
                    lastExitRefresh = Date.distantPast
                    openSafari(url: torCheckURL)
                }
            } else if current.state == "FAILED" || current.guardian.contains("DEGRADED") {
                pendingAction = nil
                pendingSince = nil
                showAlert(title: "DevFix Tunnel", message: "Safari connection failed. The Terminal window contains the detailed error.")
            }

        case .disconnect, .repair:
            if current.state == "DISCONNECTED" && current.mode == "NONE" {
                pendingAction = nil
                pendingSince = nil
                cachedExit = "—"
                lastConnectedSession = ""
            }
        }
    }

    private func pendingLabel() -> String? {
        guard let action = pendingAction else { return nil }
        switch action {
        case .connectSafari:
            if currentStatus.isBusy { return "CONNECTING…" }
            if let since = pendingSince, Date().timeIntervalSince(since) > 5 {
                return "WAITING FOR TERMINAL AUTHORIZATION…"
            }
            return "STARTING SAFARI MODE…"
        case .disconnect:
            return "DISCONNECTING…"
        case .repair:
            return "REPAIRING…"
        }
    }

    private func renderStatus() {
        let s = currentStatus
        stateItem.title = "State: \(pendingLabel() ?? s.state)"

        if s.mode == "SYSTEM_PROXY" {
            modeItem.title = "Mode: Safari Mode (System Proxy)"
        } else if s.mode == "SOCKS" {
            modeItem.title = "Mode: SOCKS (not Safari Mode)"
        } else {
            modeItem.title = "Mode: \(s.mode)"
        }

        var routeParts: [String] = []
        if !s.transport.isEmpty { routeParts.append(s.transport) }
        if !s.service.isEmpty { routeParts.append(s.service) }
        if !s.health.isEmpty { routeParts.append("Health \(s.health)") }
        if !s.guardian.isEmpty { routeParts.append(s.guardian) }
        routeItem.title = "Transport: " + (routeParts.isEmpty ? "—" : routeParts.joined(separator: " • "))
        exitItem.title = "Exit: \(cachedExit)"
        updateElapsed()
        updateStatusIcon(for: s)

        let noPending = pendingAction == nil
        connectSafariItem.isEnabled = noPending && !s.isConnected && !s.isBusy
        openSafariItem.isEnabled = noPending && s.isHealthySystemProxy
        disconnectItem.isEnabled = (s.isConnected || s.isBusy || pendingAction != nil)
        refreshExitItem.isEnabled = noPending && s.isConnected && !exitRefreshInFlight
        legacyChromeItem.isEnabled = noPending && !s.isBusy
    }

    private func updateElapsed() {
        guard currentStatus.isConnected, let start = currentStatus.connectedSince else {
            elapsedItem.title = currentStatus.isBusy ? "Connected: establishing route…" : "Connected: —"
            return
        }
        let seconds = max(0, Int(Date().timeIntervalSince(start)))
        let hours = seconds / 3600
        let minutes = (seconds % 3600) / 60
        let secs = seconds % 60
        elapsedItem.title = String(format: "Connected: %02d:%02d:%02d", hours, minutes, secs)
    }

    private func updateStatusIcon(for status: TunnelStatus) {
        guard let button = statusItem.button else { return }
        let symbol: String
        if status.guardian.contains("DEGRADED") || status.state == "FAILED" {
            symbol = "exclamationmark.triangle"
        } else if status.isHealthySystemProxy {
            symbol = "safari"
        } else if status.isConnected {
            symbol = "network"
        } else if status.isBusy || pendingAction != nil {
            symbol = "arrow.triangle.2.circlepath"
        } else {
            symbol = "network.slash"
        }
        if let image = NSImage(systemSymbolName: symbol, accessibilityDescription: "DevFix Tunnel") {
            image.isTemplate = true
            button.image = image
            button.title = ""
        } else {
            button.image = nil
            button.title = status.isHealthySystemProxy ? "Safari ✓" : "DevFix"
        }
        button.toolTip = "DevFix Tunnel — \(pendingLabel() ?? status.state)"
    }

    private func openTerminalCommand(_ command: String, action: PendingAction) {
        guard pendingAction == nil else { return }
        pendingAction = action
        pendingSince = Date()
        renderStatus()

        let escaped = command.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
        let script = "tell application \"Terminal\"\nactivate\ndo script \"\(escaped)\"\nend tell"
        CommandRunner.run("/usr/bin/osascript", ["-e", script]) { [weak self] code, output in
            guard let self = self else { return }
            if code != 0 {
                self.pendingAction = nil
                self.pendingSince = nil
                self.renderStatus()
                self.showAlert(title: "DevFix Tunnel", message: output.isEmpty ? "Could not open Terminal." : output)
            }
        }
    }

    @objc private func connectSafari() {
        if currentStatus.isHealthySystemProxy {
            openSafari(url: torCheckURL)
            return
        }
        guard currentStatus.state == "DISCONNECTED" && currentStatus.mode == "NONE" else {
            showAlert(title: "DevFix Tunnel", message: "Disconnect the current tunnel mode before starting Safari Mode.")
            return
        }
        openTerminalCommand("/usr/local/bin/devfix-tunnel connect system", action: .connectSafari)
    }

    @objc private func openSafariAction() {
        openSafari(url: torCheckURL)
    }

    private func openSafari(url: String) {
        CommandRunner.run("/usr/bin/open", ["-a", "Safari", url]) { [weak self] code, output in
            if code != 0 {
                self?.showAlert(title: "DevFix Tunnel", message: output.isEmpty ? "Safari could not be opened." : output)
            }
        }
    }

    @objc private func disconnect() {
        openTerminalCommand("/usr/local/bin/devfix-tunnel disconnect", action: .disconnect)
    }

    private func maybeRefreshExit() {
        guard currentStatus.isConnected, pendingAction == nil, !exitRefreshInFlight else { return }
        if currentStatus.session != lastConnectedSession {
            lastConnectedSession = currentStatus.session
            cachedExit = "checking…"
            lastExitRefresh = Date.distantPast
        }
        guard Date().timeIntervalSince(lastExitRefresh) >= 60 else { return }
        refreshExit(showFailure: false)
    }

    private func refreshExit(showFailure: Bool) {
        guard currentStatus.isConnected, !exitRefreshInFlight else { return }
        exitRefreshInFlight = true
        exitItem.title = "Exit: checking…"
        CommandRunner.run(cliPath, ["exit"]) { [weak self] code, output in
            guard let self = self else { return }
            self.exitRefreshInFlight = false
            self.lastExitRefresh = Date()
            if code == 0 {
                let lines = output.split(separator: "\n").map(String.init)
                let ip = lines.first(where: { $0.hasPrefix("Tor exit IP:") })?.replacingOccurrences(of: "Tor exit IP:", with: "").trimmingCharacters(in: .whitespaces)
                let country = lines.first(where: { $0.hasPrefix("Exit country:") })?.replacingOccurrences(of: "Exit country:", with: "").trimmingCharacters(in: .whitespaces)
                if let ip = ip, let country = country {
                    self.cachedExit = "\(ip) • \(country.uppercased())"
                } else {
                    self.cachedExit = "connected"
                }
            } else {
                self.cachedExit = "unavailable — retry"
                if showFailure {
                    self.showAlert(title: "Exit check failed", message: output.isEmpty ? "The tunnel is connected, but the exit lookup failed." : output)
                }
            }
            self.renderStatus()
        }
    }

    @objc private func refreshExitAction() {
        refreshExit(showFailure: true)
    }

    @objc private func openTorCheck() {
        guard currentStatus.isHealthySystemProxy else {
            showAlert(title: "DevFix Tunnel", message: "Connect Safari Mode first.")
            return
        }
        openSafari(url: torCheckURL)
    }

    @objc private func openSelectiveChrome() {
        guard pendingAction == nil else { return }
        guard FileManager.default.isExecutableFile(atPath: chromeLauncherPath) else {
            showAlert(title: "DevFix Tunnel", message: "Selective Chrome launcher is not installed.")
            return
        }
        if currentStatus.mode == "SYSTEM_PROXY" {
            showAlert(title: "DevFix Tunnel", message: "Disconnect Safari Mode before using the legacy Selective Chrome mode.")
            return
        }
        CommandRunner.run(chromeLauncherPath, [torCheckURL]) { [weak self] code, output in
            if code != 0 {
                self?.showAlert(title: "DevFix Tunnel", message: output.isEmpty ? "Selective Chrome failed." : output)
            }
            self?.refreshStatus()
        }
    }

    @objc private func copySocks() {
        guard !currentStatus.socks.isEmpty else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(currentStatus.socks, forType: .string)
    }

    @objc private func repair() {
        openTerminalCommand("/usr/local/bin/devfix-tunnel repair", action: .repair)
    }

    @objc private func refreshStatusAction() {
        refreshStatus()
    }

    @objc private func quit() {
        NSApp.terminate(nil)
    }

    private func showAlert(title: String, message: String) {
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = message
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        NSApp.activate(ignoringOtherApps: true)
        alert.runModal()
    }
}

private let app = NSApplication.shared
private let delegate = AppDelegate()
app.delegate = delegate
app.run()
