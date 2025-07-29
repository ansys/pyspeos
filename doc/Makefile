# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    = -j 1 --keep-going
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = _build
APIDIR        = api

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.install-ci-dep:
	@pip freeze | grep -q "vtk-osmesa" && is_vtk_osmesa_installed="yes" || is_vtk_osmesa_installed="no"
	@if [ "${ON_CI}" = "True" ] && [ "$$is_vtk_osmesa_installed" != "yes" ]; then \
		@echo "Removing package(s) to avoid conflicts with package(s) needed for CI/CD"; \
		pip uninstall --yes vtk; \
		@echo "Installing CI/CD required package(s)"; \
		pip install --extra-index-url https://wheels.vtk.org vtk-osmesa==9.3.1; \
	else \
		echo "Skipping vtk-osmesa installation: either not in CI (ON_CI=${ON_CI}) or already installed (is_vtk_osmesa_installed=$$is_vtk_osmesa_installed)"; \
	fi

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: .install-ci-dep Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


# customized clean due to examples gallery
clean: .install-deps
	rm -rf $(BUILDDIR)/*
	find . -type d -name $(APIDIR) -exec rm -rf {} +

#customized pdf build due to svg badges
pdf: .install-ci-dep
	@$(SPHINXBUILD) -M latex "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	cd $(BUILDDIR)/latex && latexmk -r latexmkrc -pdf *.tex -interaction=nonstopmode || true
	(test -f $(BUILDDIR)/latex/*.pdf && echo pdf exists) || exit 1

# Build HTML files and generate examples as .py files
html: .install-ci-dep
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)