import creature
import gametools
import thing

def clone():
    orc = creature.NPC('orc', __file__, aggressive=2)
    orc.set_description('burly orc', "This burly orc looks muscular and threatening."
    orc.add_adjectives('burly', 'muscular')
    orc.set_combat_vars(35, 50, 60, 40)
    orc.act_frequency = 2
   
    sword = gametools.clone("domains.centrata.orc_quest.orc_sword")
    sword.move_to(orc)

    hide = gametools.clone("domains.centrata.orc_quest.orc_hide")
    hide.move_to(orc)

    return orc