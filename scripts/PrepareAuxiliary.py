#@category APKAnalysis
for option in ['Decompiler Switch Analysis','Call Convention ID','Stack','Non-Returning Functions - Discovered']:
    try:setAnalysisOption(currentProgram,option,'false')
    except Exception:pass
