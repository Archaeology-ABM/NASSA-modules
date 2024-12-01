# Preferential Attachment Network
*by Amber Esha Jarigsma*  

This algorithm is a version of preferential attachment algorithm, generating networks where nodes (agents) are connected based on their existing number of links, simulating the "rich-get-richer" effect. It uses a lottery-style partner selection method to form links between nodes, favoring those with more existing connections. This structure can model social networks, trade networks in ancient societies, settlement hierarchies, or other real-world systems where growth follows a preferential attachment pattern.  

## License
**MIT** 

## References
For an alternative approach to implementing a preferential attachment network, see:
Wilensky, U. (2005). NetLogo Preferential Attachment model. http://ccl.northwestern.edu/netlogo/models/PreferentialAttachment. Center for Connected Learning and Computer-Based Modeling, Northwestern University, Evanston, IL.

In this model, partner selection is determined through the selection of a random link, with one of the two nodes at either end of the link serving as the new partner. This method simplifies the implementation by leveraging existing network properties, eliminating the need to explicitly calculate or store node degrees. In contrast, the implementation described here generates a weighted list of nodes based on their degrees, from which a partner is selected. While Wilensky’s approach reduces computational complexity, it sacrifices some of the flexibility and reusability offered by this more modular design, which separates key functions and explicitly tracks node attributes.

Additionally, the nw extension in NetLogo provides a built-in procedure, nw:generate-preferential-attachment, for generating scale-free networks based on the Barabási–Albert algorithm. However, as this is part of an extension and not written in NetLogo's native language, it may be less transparent and customisable compared to explicit implementations.

This implementation draws inspiration from Wilensky (2005) and the foundational work it cites. For further background on preferential attachment and scale-free networks, see:

Albert-László Barabási. Linked: The New Science of Networks. Perseus Publishing, Cambridge, Massachusetts, pages 79–92.

Albert-László Barabási & Reka Albert. "Emergence of Scaling in Random Networks." Science, Vol. 286, Issue 5439, 15 October 1999, pages 509–512.

## Further information
This model is an algorithm implemented in NetLogo. 
Users can choose how many (unattached) nodes to begin the algorithm with. 
Node size is proportional to the number of links the node has.

<img width="622" alt="Screenshot 2024-11-15 at 22 28 25" src="https://github.com/user-attachments/assets/b7b7b9fa-aeb2-49ce-bd3d-ea9482c05f2f">
