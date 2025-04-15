# TroyDestroy (DUMMY EXAMPLE) 

*by Heinrich "Dummy" Schliemann* (NASSA submission :rocket:)

This module represents a Bronze Age siege and its destructive effect on a settlement. It takes the strength of two armies, one aggressor and another defender, and calculates the level of destruction of the defenders' city. The destructive effect over the defenders' city is proportional to the two contending strengths and a constant rate per unit of strength of the aggressor matched by the defender.

## License

**MIT**

## References

Homer. 1865. The Iliad of Homer. J. Murray (trad.).

## Further information

<a title="Unknown Corinthian pottery maker BCE, Public domain, via Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Corinthian_aryballos_depicting_the_trojan_war_from_1887_jahrbuchdeskaiserich_1200x500.jpg"><img width="512" alt="Corinthian aryballos depicting the trojan war from 1887 jahrbuchdeskaiserich 1200x500" src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Corinthian_aryballos_depicting_the_trojan_war_from_1887_jahrbuchdeskaiserich_1200x500.jpg/512px-Corinthian_aryballos_depicting_the_trojan_war_from_1887_jahrbuchdeskaiserich_1200x500.jpg"></a>

This model is a algorithm implemented in NetLogo and Python 3. Disclaimer: the code might require updates since it was written in the 19th century.

Overview of the algorithm:

$$warEffect=-destructionRate*\frac{(attackerStrength)^2}{defenderStrength} $$

See full list of documentation resources in [`documentation`](documentation/tableOfContents.md).

### Acknowledgements

The "crossed swords" emoticon (⚔️) used as cover image was sourced at [Twitter Emoji (Twemoji) v14.0](https://github.com/twitter/twemoji) under CC BY 4.0.
