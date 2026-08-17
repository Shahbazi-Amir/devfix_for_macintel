import AppKit
import Foundation

private let cliPath = "/usr/local/bin/devfix-tunnel"
private let chromeLauncherPath = "/usr/local/bin/devfix-tunnel-chrome"

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

    var connectedSince: Date? {
        guard let first = session.split(separator: "-").first,
              let epoch = TimeInterval(first) else { return nil }
        return Date(timeIntervalSince1970: epoch)
    }
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
    private let routeItem = NSMenuItem(title: "Route: —", action: nil, keyEquivalent: "")
    private let elapsedItem = NSMenuItem(title: "Connected: —", action: nil, keyEquivalent: "")
    private let exitItem = NSMenuItem(title: "Exit: —", action: nil, keyEquivalent: "")
    private var connectSystemItem: NSMenuItem!
    private var connectSocksItem: NSMenuItem!
    private var selectiveChromeItem: NSMenuItem!
    private var disconnectItem: NSMenuItem!
    private var refreshTimer: Timer?
    private var elapsedTimer: Timer?
    private var currentStatus = TunnelStatus()
    private var cachedExit = "—"
    private var operationInFlight = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        configureStatusItem()
        configureMenu()
        refreshStatus()

        refreshTimer = Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { [weak self] _ in
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

        connectSystemItem = NSMenuItem(title: "Connect System Proxy…", action: #selector(connectSystem), keyEquivalent: "")
        connectSystemItem.target = self
        menu.addItem(connectSystemItem)

        connectSocksItem = NSMenuItem(title: "Connect SOCKS Only", action: #selector(connectSocks), keyEquivalent: "")
        connectSocksItem.target = self
        menu.addItem(connectSocksItem)

        selectiveChromeItem = NSMenuItem(title: "Open Selective Chrome", action: #selector(openSelectiveChrome), keyEquivalent: "")
        selectiveChromeItem.target = self
        menu.addItem(selectiveChromeItem)

        disconnectItem = NSMenuItem(title: "Disconnect", action: #selector(disconnect), keyEquivalent: "")
        disconnectItem.target = self
        menu.addItem(disconnectItem)

        menu.addItem(.separator())

        let refreshExitItem = NSMenuItem(title: "Refresh Exit IP / Country", action: #selector(refreshExit), keyEquivalent: "")
        refreshExitItem.target = self
        menu.addItem(refreshExitItem)

        let openCheckItem = NSMenuItem(title: "Open Tor Check", action: #selector(openTorCheck), keyEquivalent: "")
        openCheckItem.target = self
        menu.addItem(openCheckItem)

        let copySocksItem = NSMenuItem(title: "Copy SOCKS Address", action: #selector(copySocks), keyEquivalent: "")
        copySocksItem.target = self
        menu.addItem(copySocksItem)

        let repairItem = NSMenuItem(title: "Repair…", action: #selector(repair), keyEquivalent: "")
        repairItem.target = self
        menu.addItem(repairItem)

        menu.addItem(.separator())

        let refreshItem = NSMenuItem(title: "Refresh Status", action: #selector(refreshStatusAction), keyEquivalent: "r")
        refreshItem.target = self
        menu.addItem(refreshItem)

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
        guard !operationInFlight else { return }
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let (code, output) = CommandRunner.runSync(cliPath, ["status"])
            let parsed = self?.parseStatus(output) ?? TunnelStatus()
            DispatchQueue.main.async {
                guard let self = self else { return }
                if code == 127 {
                    self.currentStatus = TunnelStatus(state: "NOT_INSTALLED")
                } else {
                    self.currentStatus = parsed
                }
                self.renderStatus()
            }
        }
    }

    private func renderStatus() {
        let s = currentStatus
        stateItem.title = "State: \(s.state)"
        modeItem.title = "Mode: \(s.mode)"

        var routeParts: [String] = []
        if !s.transport.isEmpty { routeParts.append(s.transport) }
        if !s.service.isEmpty { routeParts.append(s.service) }
        if !s.health.isEmpty { routeParts.append(s.health) }
        if !s.guardian.isEmpty { routeParts.append(s.guardian) }
        routeItem.title = "Route: " + (routeParts.isEmpty ? "—" : routeParts.joined(separator: " • "))
        exitItem.title = "Exit: \(cachedExit)"
        updateElapsed()
        updateStatusIcon(for: s)

        let canConnect = !s.isConnected && !s.isBusy && !operationInFlight
        connectSystemItem.isEnabled = canConnect
        connectSocksItem.isEnabled = canConnect
        selectiveChromeItem.isEnabled = !operationInFlight
        disconnectItem.isEnabled = (s.isConnected || s.isBusy) && !operationInFlight
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
        } else if status.isConnected {
            symbol = "network"
        } else if status.isBusy {
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
            button.title = status.isConnected ? "DevFix ✓" : "DevFix"
        }
        button.toolTip = "DevFix Tunnel — \(status.state)"
    }

    private func beginOperation(_ label: String) {
        operationInFlight = true
        stateItem.title = "State: \(label)"
        renderStatus()
    }

    private func finishOperation(code: Int32, output: String, successMessage: String) {
        operationInFlight = false
        refreshStatus()
        if code != 0 {
            showAlert(title: "DevFix Tunnel", message: output.isEmpty ? "Command failed with code \(code)." : output)
        } else if !successMessage.isEmpty {
            statusItem.button?.toolTip = successMessage
        }
    }

    @objc private func connectSocks() {
        beginOperation("CONNECTING SOCKS…")
        CommandRunner.run(cliPath, ["connect", "socks"]) { [weak self] code, output in
            self?.finishOperation(code: code, output: output, successMessage: "SOCKS route connected")
        }
    }

    @objc private func connectSystem() {
        let script = "tell application \"Terminal\"\nactivate\ndo script \"/usr/local/bin/devfix-tunnel connect system; printf '\\\\nDevFix Tunnel command finished. You may close this window.\\\\n'\"\nend tell"
        CommandRunner.run("/usr/bin/osascript", ["-e", script]) { [weak self] code, output in
            if code != 0 {
                self?.showAlert(title: "DevFix Tunnel", message: output)
            }
            self?.refreshStatus()
        }
    }

    @objc private func openSelectiveChrome() {
        guard FileManager.default.isExecutableFile(atPath: chromeLauncherPath) else {
            showAlert(title: "DevFix Tunnel", message: "Selective Chrome launcher is not installed.")
            return
        }
        beginOperation("OPENING SELECTIVE CHROME…")
        CommandRunner.run(chromeLauncherPath, ["https://check.torproject.org/"]) { [weak self] code, output in
            self?.finishOperation(code: code, output: output, successMessage: "Selective Chrome launched")
        }
    }

    @objc private func disconnect() {
        beginOperation("DISCONNECTING…")
        CommandRunner.run(cliPath, ["disconnect"]) { [weak self] code, output in
            self?.cachedExit = "—"
            self?.finishOperation(code: code, output: output, successMessage: "Disconnected safely")
        }
    }

    @objc private func refreshExit() {
        guard currentStatus.isConnected else {
            showAlert(title: "DevFix Tunnel", message: "Connect the tunnel before checking the exit.")
            return
        }
        exitItem.title = "Exit: checking…"
        CommandRunner.run(cliPath, ["exit"]) { [weak self] code, output in
            guard let self = self else { return }
            if code == 0 {
                let ip = output.split(separator: "\n").first(where: { $0.hasPrefix("Tor exit IP:") }).map { String($0).replacingOccurrences(of: "Tor exit IP:", with: "").trimmingCharacters(in: .whitespaces) }
                let country = output.split(separator: "\n").first(where: { $0.hasPrefix("Exit country:") }).map { String($0).replacingOccurrences(of: "Exit country:", with: "").trimmingCharacters(in: .whitespaces) }
                if let ip = ip, let country = country {
                    self.cachedExit = "\(ip) • \(country.uppercased())"
                } else {
                    self.cachedExit = output.trimmingCharacters(in: .whitespacesAndNewlines)
                }
            } else {
                self.cachedExit = "unavailable"
                self.showAlert(title: "Exit check failed", message: output)
            }
            self.exitItem.title = "Exit: \(self.cachedExit)"
        }
    }

    @objc private func openTorCheck() {
        if currentStatus.mode == "SOCKS" {
            openSelectiveChrome()
            return
        }
        guard let url = URL(string: "https://check.torproject.org/") else { return }
        NSWorkspace.shared.open(url)
    }

    @objc private func copySocks() {
        guard !currentStatus.socks.isEmpty else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(currentStatus.socks, forType: .string)
    }

    @objc private func repair() {
        let script = "tell application \"Terminal\"\nactivate\ndo script \"/usr/local/bin/devfix-tunnel repair; printf '\\\\nDevFix Tunnel repair finished. You may close this window.\\\\n'\"\nend tell"
        CommandRunner.run("/usr/bin/osascript", ["-e", script]) { [weak self] _, _ in
            self?.refreshStatus()
        }
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

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
