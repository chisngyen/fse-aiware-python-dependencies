# Render pipeline — pure Manim, 3blue1brown-style
#
# Usage:
#   make list                              # list all scene names
#   make preview SCENE=DependencyDomino    # 480p15 fast iteration
#   make hd      SCENE=DependencyDomino    # 1080p60 final
#   make all                               # render every scene at HD
#   make concat                            # ffmpeg-concat into final mp4
#   make clean                             # wipe intermediate manim caches

MANIM      ?= manim
OUT        ?= renders
SCENES_PY  := manim/scenes.py

# Scene order — matches manuscripts/slide/main.tex (Problem → Solution → Results → Limits).
SCENES := Title Outline Context ProblemIO DependencyDomino \
          CombinatorialExplosion Datasets RelatedWorkApproaches RelatedWorkTimeline \
          MemresPipeline MemresLimits ParadigmShift MultiAgentLoop \
          CSPFormulation SessionLearning PassRates ErrorElim \
          OpenVsClosed SpeedRaceAndAblation HardFloor ArchLimits \
          FutureWork Summary ThankYou

.PHONY: all preview hd clean concat list narrate

list:
	@echo "Scenes (in narrative order):" && for s in $(SCENES); do echo "  - $$s"; done

preview:
	cd manim && $(MANIM) -pql $(notdir $(SCENES_PY)) $(SCENE) --media_dir ../$(OUT)

hd:
	cd manim && $(MANIM) -qh $(notdir $(SCENES_PY)) $(SCENE) --media_dir ../$(OUT)

all:
	@for s in $(SCENES); do \
	  echo "=== Rendering $$s ==="; \
	  (cd manim && $(MANIM) -qh $(notdir $(SCENES_PY)) $$s --media_dir ../$(OUT)); \
	done

FFMPEG_BIN ?= ffmpeg

concat:
	@echo "Building concat list..." && \
	rm -f $(OUT)/concat.txt && \
	for s in $(SCENES); do \
	  f=$$(find $(OUT)/videos -name "$$s.mp4" | head -n1); \
	  if [ -n "$$f" ]; then echo "file '$$f'" >> $(OUT)/concat.txt; \
	  else echo "MISSING: $$s.mp4"; fi; \
	done && \
	cat $(OUT)/concat.txt && \
	$(FFMPEG_BIN) -y -loglevel error -f concat -safe 0 -i $(OUT)/concat.txt -c copy $(OUT)/cgar_presentation.mp4 && \
	echo "==> $(OUT)/cgar_presentation.mp4"

narrate:
	python build_narrated.py

clean:
	rm -rf $(OUT)/videos $(OUT)/images $(OUT)/Tex $(OUT)/texts $(OUT)/concat.txt
