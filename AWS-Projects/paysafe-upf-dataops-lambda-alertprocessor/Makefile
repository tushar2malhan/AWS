
.PHONY: help lint lint-fix image push run deploy clean
.DEFAULT_GOAL := help
python_error_file = code_errors.txt

test: ## 🧪  Run tests
    
	flake8 --version
	flake8 . --exit-zero 
	flake8 . --exit-zero > $(python_error_file)

plan: ## 📝  Plan terraform
	
	echo "Printing all files in the dev directory"
	cd automation/ca-central-1/mon-dev-blue/lambda && \
	ls -la && \
	terraform init -input=false --upgrade  && \
	terraform validate && \
	touch tfplan && \
	terraform plan -out tfplan -input=false 

dev/deploy: ## 🚀  Apply terraform in Dev

	echo "Deployment in dev account"
	cd automation/ca-central-1/mon-dev-blue/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out tfplan -input=false && \
	terraform apply -input=false -auto-approve tfplan

prep/deploy: ## 🚀  Apply terraform in Prep
	
	echo "Deployment in Prep account"
	cd automation/ca-central-1/mon-prep-blue/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prep-blue-tfplan -input=false  && \
	terraform apply -input=false -auto-approve mon-prep-blue-tfplan

prod/deploy: ## 🚀  Apply terraform in Prod
	
	echo "Deployment in Prod account"
	cd automation/ca-central-1/mon-prod-blue/lambda && \
	terraform init -input=false --upgrade  && \
	terraform plan -out mon-prod-blue-tfplan -input=false  && \
	terraform apply -input=false -auto-approve mon-prod-blue-tfplan
	
clean:  ## 🧹 Clean up project

	rm -fr .terraform
	rm -rf .venv
	rm -rf .pytest_cache


# ============================================================================
