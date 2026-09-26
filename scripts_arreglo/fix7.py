import pcbnew
B = pcbnew.LoadBoard("T8Sequencer.kicad_pcb")
for z in B.Zones():
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save("T8Sequencer.kicad_pcb")
print("islas aisladas eliminadas y plano rerrellenado")
