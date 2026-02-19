#!/bin/bash
set -euo pipefail

# Calculate script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FORMATTER_CONFIG="$DIR/../eclipse/synventis-code-formatter.xml"

# Help message
function show_help {
    echo "Usage: $0 [options] [maven-args]"
    echo ""
    echo "Formats Java code using the Synventis code formatter."
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "All other arguments are passed to the Maven command."
}

# Parse arguments for help
for arg in "$@"; do
    case $arg in
        -h|--help)
        show_help
        exit 0
        ;;
    esac
done

# Check if formatter config exists
if [ ! -f "$FORMATTER_CONFIG" ]; then
    echo "Error: Formatter config file not found at $FORMATTER_CONFIG"
    exit 1
fi

mvn net.revelc.code.formatter:formatter-maven-plugin:2.23.0:format \
    -Dformatter.configFile="$FORMATTER_CONFIG" \
    -Dencoding=UTF-8 \
    -Dproject.build.sourceEncoding=UTF-8 \
    "$@"
