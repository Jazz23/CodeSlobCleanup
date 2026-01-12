HAgent Projects https://github.com/masc-ucsc/hagent
ESP32 Boards
name: esp32board
Objective: HAgent currently has ESP32 support for only one type of board. Extend MCP support to multiple boards, and go beyond the ESP-IDF (ESP32) to also support STM32 boards. Some boards should have multiple controllers.
Team Size: 1
	  Sri S <ssenthi7@ucsc.edu>
Few-Shot Memory Layer
Objective: Improve the hagent/tool/memory so that it uses https://github.com/sirasagi62/code-chopper and possibly FAISS. The goal is to find somewhat similar code/problems in the database so that they can be provided as examples in context.
The concept could be similar to https://github.com/vitali87/code-graph-rag but instead of using natural language on the search, the search is from code to code, to look for related/similar code functionality/snippets.
