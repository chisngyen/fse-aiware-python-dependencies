# Render pipeline — Manim scenes + Blender shots → final video
#
# Usage:
#   make preview SCENE=DependencyDomino   # 480p15 fast iteration
#   make hd      SCENE=DependencyDomino   # 1080p60 final
#   make all                              # render every scene at HD
#   make blender-11                       # render slide 11 Blender shot
#   make concat                           # ffmpeg-concat into final mp4

MANIM      ?= manim
BLENDER    ?= blender
OUT        ?= renders
SCENES_PY  := manim/scenes.py

# Order matters for `concat` — keeps narrative sequence
SCENES := Title Outline ProblemIO Requirements Datasets \
          DependencyDomino MemresPipeline MemresLimits \
          CSPFormulation BacktrackingTree CGARArchitecture \
          FailureCases PassRates SpeedRace ErrorElim Ablation \
          ThankYou

.PHONY: all preview hd clean blender-11 blender-01 concat list

list:
	@echo "Scenes (in order):" && for s in $(SCENES); do echo "  - $$s"; done

preview:
	cd manim && $(MANIM) -pql $(notdir $(SCENES_PY)) $(SCENE) --media_dir ../$(OUT)

hd:
	cd manim && $(MANIM) -qh $(notdir $(SCENES_PY)) $(SCENE) --media_dir ../$(OUT)

all:
	@for s in $(SCENES); do \
	  echo "=== Rendering $$s ==="; \
	  cd manim && $(MANIM) -qh $(notdir $(SCENES_PY)) $$s --media_dir ../$(OUT) && cd ..; \
	done

# Render Blender hero shots from saved .blend files
# (These .blend were built interactively via the official Blender MCP plugin.)
blender-01:
	$(BLENDER) -b $(OUT)/01_title.blend -a

blender-06:
	$(BLENDER) -b $(OUT)/06_dominoes.blend -a

blender-11:
	$(BLENDER) -b $(OUT)/11_agents.blend -a

# Composite all Blender PNG sequences → mp4 (incl. Option C freeze for slide 11)
blender-compose:
	bash compose.sh

# Hero slots that come from Blender (override Manim equivalents in concat)
# Format:  <SceneName>=<mp4_path_relative_to_renders>
BLENDER_OVERRIDES := Title=01_title.mp4 DependencyDomino=06_dominoes.mp4 CGARArchitecture=11_agents.mp4

# Concat all scenes into the master video. Blender hero shots override Manim
# equivalents for slides 1, 6, 11.
FFMPEG_BIN ?= C:/Program\ Files/iGameCenter/SAVIConverter/tools/ffmpeg.exe

concat:
	@echo "Building concat list (Blender overrides for hero shots)..." && \
	rm -f $(OUT)/concat.txt && \
	for s in $(SCENES); do \
	  override=$$(echo "$(BLENDER_OVERRIDES)" | tr ' ' '\n' | grep "^$$s=" | cut -d= -f2); \
	  if [ -n "$$override" ] && [ -f $(OUT)/$$override ]; then \
	    f=$(OUT)/$$override; echo "[hero] $$s -> $$f"; \
	  else \
	    f=$$(find $(OUT)/videos -name "$$s.mp4" | head -n1); \
	  fi; \
	  if [ -n "$$f" ]; then echo "file '$$f'" >> $(OUT)/concat.txt; \
	  else echo "MISSING: $$s.mp4"; fi; \
	done && \
	cat $(OUT)/concat.txt && \
	$(FFMPEG_BIN) -y -loglevel error -f concat -safe 0 -i $(OUT)/concat.txt -c copy $(OUT)/cgar_presentation.mp4 && \
	echo "==> $(OUT)/cgar_presentation.mp4"

clean:
	rm -rf $(OUT)/videos $(OUT)/images $(OUT)/Tex $(OUT)/texts $(OUT)/concat.txt
