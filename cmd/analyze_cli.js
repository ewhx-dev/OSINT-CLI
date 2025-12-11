const { performance } = require('perf_hooks');

const GO_GATEWAY_URL = 'http://localhost:8080/analyze?target=';

function formatReportForCLI(reportData) {
    const check = '\x1b[32m✔\x1b[0m'; // Green
    const xMark = '\x1b[31m✖\x1b[0m'; // Red
    const warning = '\x1b[33m▲\x1b[0m'; // Yellow
    const info = '\x1b[36m▶\x1b[0m'; // Cyan
    const target = reportData.target || 'N/A';
    
    const cacheStatus = reportData.is_cached ? `\x1b[43m\x1b[30m CACHED \x1b[0m` : `\x1b[42m\x1b[30m LIVE SCAN \x1b[0m`;

    let output = `\n\n--- 🕵️ OSINT Report: ${target} ${cacheStatus} ---\n`;
    output += `SUMMARY: ${reportData.summary || 'No summary.'}\n`;
    output += `Timestamp: ${reportData.timestamp}\n\n`;

    output += `--- [ 🌐 Domain Info ] ---\n`;
    const domainInfo = reportData.domain_results;
    if (domainInfo) {
        const regStatus = domainInfo.is_registered ? `${check} Registered` : `${xMark} NOT Registered`;
        output += `  Status: ${regStatus}\n`;
        output += `  Owner (Simulated): ${domainInfo.owner_simulated || 'N/A'}\n`;
        output += `  Expiration: ${domainInfo.expiration_date || 'N/A'}\n\n`;
    } else {
        output += `  ${info} Domain check skipped or target is username.\n\n`;
    }

    output += `--- [ 📸 Social Media & Profiles ] ---\n`;
    const socialHits = reportData.social_media_hits || [];
    socialHits.forEach(hit => {
        const statusIcon = hit.status === 'FOUND' ? check : xMark;
        output += `  ${statusIcon} ${hit.platform}: ${hit.url_found || 'Not Found / Private'}\n`;
    });
    output += "\n";

    output += `--- [ ⚠️ Vulnerabilities & Risks ] ---\n`;
    const vulnHits = reportData.vulnerability_hits || [];
    if (vulnHits.length > 0) {
        vulnHits.forEach(hit => {
            const icon = hit.severity === 'CRITICAL' ? xMark : warning;
            output += `  ${icon} [${hit.source} - ${hit.severity}]: ${hit.description}\n`;
        });
    } else {
        output += `  ${check} No significant vulnerabilities found.\n`;
    }
    output += "\n";

    output += `--- [ 🔎 Web Search & Dorking ] ---\n`;
    const searchData = reportData.web_search_data || [];
    searchData.forEach(hit => {
        if (hit.result_type === "Sensitive File Exposure") {
             output += `  ${warning} Dork Hit (${hit.source}): ${(Array.isArray(hit.data) ? hit.data.join(', ') : JSON.stringify(hit.data))}\n`;
        } else if (hit.result_type === "Page Count") {
             const pages = (hit.data && hit.data.pages) ? hit.data.pages : (hit.data.pages || 'N/A');
             output += `  ${info} ${hit.source}: Estimated pages indexed: ${pages}\n`;
        } else {
             output += `  ${info} ${hit.source}: ${JSON.stringify(hit.data)}\n`;
        }
    });

    output += `\n----------------------------------------\n`;
    return output;
}

async function main() {
    const target = process.argv[2];

    if (!target) {
        console.error('Usage: node analyze_cli.js <target_domain_or_username>');
        console.error('\nExample: node analyze_cli.js secure-company-dev');
        process.exit(1);
    }

    console.log(`\nStarting deep scan for target: \x1b[36m${target}\x1b[0m...`);
    const startTime = performance.now();
    
    try {
        const response = await fetch(GO_GATEWAY_URL + encodeURIComponent(target));
        let reportData = null;
        try {
            reportData = await response.json();
        } catch (err) {
            console.error(`\n❌ Invalid JSON response from gateway. HTTP ${response.status}`);
            const text = await response.text().catch(()=>"<unable to read body>");
            console.error("Response body:", text);
            return;
        }

        if (response.status === 429) {
             console.error(`\n❌ Rate Limit Error (429): Too many requests. Wait 3 seconds and try again.`);
             return;
        }

        if (!response.ok) {
            console.error(`\n❌ HTTP Error ${response.status}: ${reportData.detail || reportData.message || 'Service Error'}`);
            return;
        }

        const endTime = performance.now();
        
        console.log(formatReportForCLI(reportData));
        console.log(`Total analysis time: \x1b[33m${((endTime - startTime) / 1000).toFixed(2)}s\x1b[0m`);

    } catch (error) {
        console.error(`\n❌ Connection Error. Ensure the Go Gateway is running on port 8080 and reachable.`);
        console.error(`Detail: ${error.message}`);
    }
}

main();