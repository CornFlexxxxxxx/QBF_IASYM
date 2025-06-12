#!/usr/bin/env python3
"""
QBF Logic System - Clean Version
Text to QBF conversion with LLM + TweetyProject QBF solving
"""

import subprocess
import tempfile
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from pathlib import Path
import shutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QBFResult(Enum):
    SATISFIABLE = "SATISFIABLE"
    UNSATISFIABLE = "UNSATISFIABLE"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

@dataclass
class QBFFormula:
    formula: str
    variables: List[str]
    quantifiers: List[Tuple[str, str]]
    description: str = None

@dataclass
class QBFEvaluationResult:
    formula: QBFFormula
    result: QBFResult
    execution_time: float
    solver_output: str
    error_message: str = None

class DepQBFSolver:
    """Dedicated QBF solver using DepQBF"""
    
    def __init__(self):
        self.depqbf_path = self._find_or_install_depqbf()
        if not self.depqbf_path:
            raise RuntimeError("DepQBF solver not available")
    
    def _find_or_install_depqbf(self) -> str:
        """Find or install DepQBF solver"""
        # Check if depqbf is already in PATH
        depqbf_path = shutil.which("depqbf")
        if depqbf_path:
            logger.info(f"Found DepQBF at: {depqbf_path}")
            return depqbf_path
        
        # Try to install via package manager
        try:
            # Try apt (Ubuntu/Debian)
            result = subprocess.run(["which", "apt"], capture_output=True)
            if result.returncode == 0:
                logger.info("Installing DepQBF via apt...")
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "depqbf"], check=True)
                return shutil.which("depqbf")
        except subprocess.CalledProcessError:
            pass
        
        # Try to download and compile from source
        try:
            return self._compile_depqbf_from_source()
        except Exception as e:
            logger.error(f"Failed to install DepQBF: {e}")
            return None
    
    def _compile_depqbf_from_source(self) -> str:
        """Download and compile DepQBF from source"""
        import urllib.request
        import tarfile
        
        depqbf_dir = Path("./depqbf")
        if depqbf_dir.exists():
            shutil.rmtree(depqbf_dir)
        
        depqbf_dir.mkdir()
        
        # Download DepQBF
        url = "http://lonsing.github.io/depqbf/depqbf-6.03.tar.gz"
        tar_path = depqbf_dir / "depqbf.tar.gz"
        
        logger.info("Downloading DepQBF...")
        urllib.request.urlretrieve(url, tar_path)
        
        # Extract
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(depqbf_dir)
        
        # Find extracted directory
        extracted_dir = None
        for item in depqbf_dir.iterdir():
            if item.is_dir() and item.name.startswith("depqbf"):
                extracted_dir = item
                break
        
        if not extracted_dir:
            raise RuntimeError("Failed to extract DepQBF")
        
        # Compile
        logger.info("Compiling DepQBF...")
        subprocess.run(["make"], cwd=extracted_dir, check=True)
        
        depqbf_binary = extracted_dir / "depqbf"
        if depqbf_binary.exists():
            # Make it executable
            os.chmod(depqbf_binary, 0o755)
            logger.info(f"DepQBF compiled successfully: {depqbf_binary}")
            return str(depqbf_binary)
        
        raise RuntimeError("DepQBF compilation failed")
    
    def evaluate_qbf(self, formula: QBFFormula) -> QBFEvaluationResult:
        """Evaluate QBF using DepQBF solver"""
        import time
        start_time = time.time()
        
        try:
            # Convert to QDIMACS format
            qdimacs_content = self._to_qdimacs(formula)
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.qdimacs', delete=False) as f:
                f.write(qdimacs_content)
                temp_file = f.name
            
            try:
                # Run DepQBF
                cmd = [self.depqbf_path, temp_file]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                execution_time = time.time() - start_time
                
                # Parse result
                qbf_result = self._parse_depqbf_output(result.stdout, result.stderr, result.returncode)
                
                return QBFEvaluationResult(
                    formula=formula,
                    result=qbf_result,
                    execution_time=execution_time,
                    solver_output=f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                    error_message=result.stderr if result.returncode != 0 else None
                )
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            return QBFEvaluationResult(
                formula=formula,
                result=QBFResult.ERROR,
                execution_time=time.time() - start_time,
                solver_output="",
                error_message=str(e)
            )
    
    def _to_qdimacs(self, formula: QBFFormula) -> str:
        """Convert QBF formula to QDIMACS format"""
        
        # Create variable mapping
        var_to_num = {var: i+1 for i, var in enumerate(formula.variables)}
        num_vars = len(formula.variables)
        
        # Convert formula to CNF clauses
        cnf_clauses = self._formula_to_cnf(formula.formula, var_to_num)
        num_clauses = len(cnf_clauses)
        
        # Build QDIMACS
        lines = []
        lines.append(f"p cnf {num_vars} {num_clauses}")
        
        # Add quantifiers
        current_quantifier = None
        current_vars = []
        
        for quant_type, var in formula.quantifiers:
            var_num = var_to_num[var]
            
            if quant_type != current_quantifier:
                # Output previous quantifier block
                if current_quantifier and current_vars:
                    quant_symbol = "e" if current_quantifier == "exists" else "a"
                    vars_str = " ".join(map(str, current_vars))
                    lines.append(f"{quant_symbol} {vars_str} 0")
                
                # Start new quantifier block
                current_quantifier = quant_type
                current_vars = [var_num]
            else:
                current_vars.append(var_num)
        
        # Output final quantifier block
        if current_quantifier and current_vars:
            quant_symbol = "e" if current_quantifier == "exists" else "a"
            vars_str = " ".join(map(str, current_vars))
            lines.append(f"{quant_symbol} {vars_str} 0")
        
        # Add clauses
        for clause in cnf_clauses:
            clause_str = " ".join(map(str, clause)) + " 0"
            lines.append(clause_str)
        
        return "\n".join(lines)
    
    def _formula_to_cnf(self, formula: str, var_to_num: Dict[str, int]) -> List[List[int]]:
        """Convert propositional formula to CNF clauses - FIXED ORDER"""
        
        # Handle simple cases first
        original_formula = formula.strip()
        print(f"DEBUG CNF: Original formula: '{original_formula}'")
        
        # Normalize formula syntax first - ALWAYS
        formula = self._normalize_formula_syntax(original_formula)
        print(f"DEBUG CNF: Normalized formula: '{formula}'")
        
        # Simple literal
        if formula in var_to_num:
            print(f"DEBUG CNF: Simple literal '{formula}' -> {[[var_to_num[formula]]]}")
            return [[var_to_num[formula]]]
        
        # Negated literal  
        if formula.startswith('!') and formula[1:] in var_to_num:
            print(f"DEBUG CNF: Negated literal '{formula}' -> {[[-var_to_num[formula[1:]]]]}")
            return [[-var_to_num[formula[1:]]]]
        
        # CRITICAL FIX: Handle || BEFORE && to preserve parentheses structure
        # Handle x || y pattern (OR creates single clause with multiple literals)
        if ' || ' in formula:
            parts = formula.split(' || ')
            print(f"DEBUG CNF: Split on ' || ': {parts}")
            
            # Check if this is a complex OR with parentheses - handle with distributive law
            has_complex_parts = any(part.strip().startswith('(') and part.strip().endswith(')') for part in parts)
            print(f"DEBUG CNF: Has complex parts with parentheses: {has_complex_parts}")
            
            if has_complex_parts:
                # For complex OR like (x && !y) || (!x && y), use distributive conversion
                print(f"DEBUG CNF: Using complex OR conversion (distributive law)")
                return self._convert_complex_or_to_cnf(parts, var_to_num)
            else:
                # Simple OR - just combine literals
                print(f"DEBUG CNF: Processing simple OR")
                clause = []
                for i, part in enumerate(parts):
                    part = part.strip()
                    print(f"DEBUG CNF: Processing OR part {i+1}: '{part}'")
                    if part in var_to_num:
                        clause.append(var_to_num[part])
                        print(f"DEBUG CNF: Added positive literal: {var_to_num[part]}")
                    elif part.startswith('!') and part[1:] in var_to_num:
                        clause.append(-var_to_num[part[1:]])
                        print(f"DEBUG CNF: Added negative literal: {-var_to_num[part[1:]]}")
                    else:
                        # Try to parse recursively for simple cases
                        print(f"DEBUG CNF: Trying recursive parse for: '{part}'")
                        sub_cnf = self._formula_to_cnf(part, var_to_num)
                        if len(sub_cnf) == 1 and len(sub_cnf[0]) == 1:
                            clause.append(sub_cnf[0][0])
                            print(f"DEBUG CNF: Added from recursive parse: {sub_cnf[0][0]}")
                        else:
                            logger.warning(f"Complex part in simple OR: {part}")
                            print(f"DEBUG CNF: Failed to parse '{part}', using tautology fallback")
                            return [[1, -1]]  # fallback
                print(f"DEBUG CNF: Final OR clause: {clause}")
                return [clause] if clause else [[1, -1]]

        # Handle x && !y pattern (AND creates multiple clauses) - AFTER checking for ||
        if ' && ' in formula:
            parts = formula.split(' && ')
            print(f"DEBUG CNF: Split on ' && ': {parts}")
            clauses = []
            for i, part in enumerate(parts):
                part = part.strip()
                print(f"DEBUG CNF: Processing AND part {i+1}: '{part}'")
                if part in var_to_num:
                    clauses.append([var_to_num[part]])
                    print(f"DEBUG CNF: Simple var '{part}' -> clause {[var_to_num[part]]}")
                elif part.startswith('!') and part[1:] in var_to_num:
                    clauses.append([-var_to_num[part[1:]]])
                    print(f"DEBUG CNF: Negated var '{part}' -> clause {[-var_to_num[part[1:]]]}")
                else:
                    # Handle more complex sub-expressions recursively
                    print(f"DEBUG CNF: Recursively processing complex part: '{part}'")
                    sub_clauses = self._formula_to_cnf(part, var_to_num)
                    clauses.extend(sub_clauses)
                    print(f"DEBUG CNF: Sub-clauses: {sub_clauses}")
            print(f"DEBUG CNF: Final AND clauses: {clauses}")
            return clauses

        # Handle parentheses - AFTER checking for operators
        if formula.startswith('(') and formula.endswith(')'):
            print(f"DEBUG CNF: Removing outer parentheses from: '{formula}'")
            # Check if these are balanced outer parentheses
            inner = formula[1:-1].strip()
            paren_count = 0
            for char in inner:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count < 0:
                        break
            
            if paren_count == 0:  # Balanced, safe to remove outer parens
                print(f"DEBUG CNF: Inner formula after removing parens: '{inner}'")
                return self._formula_to_cnf(inner, var_to_num)
            else:
                print(f"DEBUG CNF: Unbalanced parentheses, keeping as-is")
        
        # Single variable fallback
        if formula in var_to_num:
            print(f"DEBUG CNF: Final fallback - single variable '{formula}' -> {[[var_to_num[formula]]]}")
            return [[var_to_num[formula]]]
        
        # Fallback: create a tautology
        logger.warning(f"Unknown formula pattern: {formula}, creating tautology")
        print(f"DEBUG CNF: UNKNOWN PATTERN '{formula}' - using tautology fallback [[1, -1]]")
        return [[1, -1]]  # Always true

    def _convert_complex_or_to_cnf(self, parts: List[str], var_to_num: Dict[str, int]) -> List[List[int]]:
        """Convert complex OR with parentheses to CNF using distributive law"""
        
        print(f"DEBUG COMPLEX OR: Input parts: {parts}")
        
        cnf_parts = []
        
        for i, part in enumerate(parts):
            part = part.strip()
            print(f"DEBUG COMPLEX OR: Processing part {i+1}: '{part}'")
            
            # Remove outer parentheses if present
            if part.startswith('(') and part.endswith(')'):
                part = part[1:-1].strip()
                print(f"DEBUG COMPLEX OR: Removed outer parens: '{part}'")
            
            # Convert this part to CNF
            print(f"DEBUG COMPLEX OR: Converting to CNF: '{part}'")
            part_cnf = self._formula_to_cnf(part, var_to_num)
            print(f"DEBUG COMPLEX OR: Part CNF result: {part_cnf}")
            cnf_parts.append(part_cnf)
        
        print(f"DEBUG COMPLEX OR: All CNF parts: {cnf_parts}")
        
        # Apply distributive law for multiple parts
        # For (A && B) || (C && D) || E, convert to CNF using distributive expansion
        result_cnf = []
        
        # Start with the first part
        if not cnf_parts:
            return [[1, -1]]  # Fallback
        
        # Initialize with first part
        current_combinations = cnf_parts[0]
        print(f"DEBUG COMPLEX OR: Starting with first part: {current_combinations}")
        
        # For each additional part, apply distributive law
        for i in range(1, len(cnf_parts)):
            next_part = cnf_parts[i]
            print(f"DEBUG COMPLEX OR: Combining with part {i+1}: {next_part}")
            
            new_combinations = []
            
            # For each existing combination, combine with each clause from the next part
            for existing_clause in current_combinations:
                for new_clause in next_part:
                    # Combine clauses: [A] || [C] = [A, C]
                    combined_clause = existing_clause + new_clause
                    new_combinations.append(combined_clause)
                    print(f"DEBUG COMPLEX OR: Combined: {existing_clause} + {new_clause} = {combined_clause}")
            
            current_combinations = new_combinations
            print(f"DEBUG COMPLEX OR: Current combinations after part {i+1}: {current_combinations}")
        
        print(f"DEBUG COMPLEX OR: Final result CNF: {current_combinations}")
        return current_combinations
    
    def _normalize_formula_syntax(self, formula: str) -> str:
        """Normalize different formula syntax variations - FIXED SPACING"""
        import re
        
        # Step 1: Replace negation symbols
        formula = formula.replace('~', '!')
        formula = formula.replace('¬', '!')
        
        # Step 2: Simple character-by-character processing
        result = []
        i = 0
        while i < len(formula):
            char = formula[i]
            
            if char == '&':
                # Check if next char is also &
                if i + 1 < len(formula) and formula[i + 1] == '&':
                    result.append(' && ')  # SPACES BEFORE AND AFTER
                    i += 2
                else:
                    result.append(' && ')  # SPACES BEFORE AND AFTER
                    i += 1
            elif char == '|':
                # Check if next char is also |
                if i + 1 < len(formula) and formula[i + 1] == '|':
                    result.append(' || ')  # SPACES BEFORE AND AFTER
                    i += 2
                else:
                    result.append(' || ')  # SPACES BEFORE AND AFTER
                    i += 1
            elif char == '!':
                result.append('!')
                i += 1
            elif char == '(' or char == ')':
                result.append(char)
                i += 1
            elif char.isspace():
                if result and result[-1] != ' ' and result[-1] not in '()':
                    result.append(' ')
                i += 1
            else:
                result.append(char)
                i += 1
        
        normalized = ''.join(result)
        
        # Final cleanup - but preserve operator spacing
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # CRITICAL: Ensure proper spacing around operators
        normalized = re.sub(r'\s*&&\s*', ' && ', normalized)
        normalized = re.sub(r'\s*\|\|\s*', ' || ', normalized)
        
        # Fix parentheses spacing
        normalized = re.sub(r'\s*\(\s*', '(', normalized)
        normalized = re.sub(r'\s*\)\s*', ')', normalized)
        
        # IMPORTANT: Fix patterns like )||( -> ) || (
        normalized = re.sub(r'\)\|\|', ') ||', normalized)
        normalized = re.sub(r'\|\|\(', '|| (', normalized)
        
        return normalized
    
    def _parse_depqbf_output(self, stdout: str, stderr: str, returncode: int) -> QBFResult:
        """Parse DepQBF output to determine result"""
        
        # DepQBF returns:
        # - 10 for SAT (satisfiable)
        # - 20 for UNSAT (unsatisfiable) 
        # - 0 for unknown/timeout
        
        if returncode == 10:
            return QBFResult.SATISFIABLE
        elif returncode == 20:
            return QBFResult.UNSATISFIABLE
        elif returncode == 0:
            return QBFResult.UNKNOWN
        else:
            return QBFResult.ERROR

class TweetyQBFSolver:
    def __init__(self, jar_path: str):
        self.jar_path = Path(jar_path)
        if not self.jar_path.exists():
            raise FileNotFoundError(f"TweetyProject JAR not found: {jar_path}")
        
        subprocess.run(["java", "-version"], capture_output=True, check=True)
        
        self.bridge_dir = Path("tweety_bridge")
        self.bridge_dir.mkdir(exist_ok=True)
        self._create_bridge()
    
    def _create_bridge(self):
        java_code = '''import org.tweetyproject.logics.qbf.parser.QbfParser;
import org.tweetyproject.logics.qbf.reasoner.NaiveQbfReasoner;
import org.tweetyproject.logics.pl.syntax.PlBeliefSet;
import org.tweetyproject.logics.pl.syntax.PlFormula;
import org.tweetyproject.logics.pl.syntax.Contradiction;
import java.io.*;
import java.util.*;

public class TweetyQBFBridge {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("ERROR: No input provided");
            System.exit(1);
        }
        
        try {
            String qbfContent = args[0];
            System.err.println("DEBUG: Processing QBF content: " + qbfContent);
            
            File tempFile = File.createTempFile("qbf_", ".qbf");
            System.err.println("DEBUG: Created temp file: " + tempFile.getAbsolutePath());
            
            try (FileWriter writer = new FileWriter(tempFile)) {
                writer.write(qbfContent);
            }
            System.err.println("DEBUG: Successfully wrote to temp file");
            
            // Read back the file to verify
            try (BufferedReader reader = new BufferedReader(new FileReader(tempFile))) {
                String line;
                System.err.println("DEBUG: File contents:");
                while ((line = reader.readLine()) != null) {
                    System.err.println("DEBUG: " + line);
                }
            }
            
            QbfParser parser = new QbfParser();
            PlBeliefSet beliefSet = (PlBeliefSet) parser.parseBeliefBaseFromFile(tempFile.getAbsolutePath());
            System.err.println("DEBUG: Parsed belief set, size: " + beliefSet.size());
            
            if (!beliefSet.isEmpty()) {
                PlFormula formula = (PlFormula) beliefSet.iterator().next();
                System.err.println("DEBUG: Got formula: " + formula.getClass().getName());
                System.err.println("DEBUG: Formula toString: " + formula.toString());
                
                NaiveQbfReasoner reasoner = new NaiveQbfReasoner();
                
                // For QBF, we need to check if the formula is a tautology
                // If reasoner.query(beliefSet, formula) returns true, it means the formula is satisfiable
                // But for universally quantified formulas, we want to know if it's always true
                
                // Create a new belief set with just the formula
                PlBeliefSet singleFormulaSet = new PlBeliefSet();
                singleFormulaSet.add(formula);
                
                // Check if the formula is satisfiable
                boolean isSatisfiable = reasoner.query(singleFormulaSet, formula);
                System.err.println("DEBUG: Formula satisfiability: " + isSatisfiable);
                
                // For contradiction check, we test if adding the formula leads to inconsistency
                Contradiction contradiction = new Contradiction();
                boolean isInconsistent = reasoner.query(singleFormulaSet, contradiction);
                System.err.println("DEBUG: Formula leads to contradiction: " + isInconsistent);
                
                // A universally quantified formula like ∀x (x ∧ ¬x) should be unsatisfiable
                // because x ∧ ¬x is always false regardless of x's value
                if (isInconsistent || !isSatisfiable) {
                    System.out.println("RESULT: UNSATISFIABLE");
                } else {
                    System.out.println("RESULT: SATISFIABLE");
                }
            } else {
                System.err.println("DEBUG: Belief set is empty!");
                System.out.println("RESULT: ERROR");
            }
            
            boolean deleted = tempFile.delete();
            System.err.println("DEBUG: Temp file deleted: " + deleted);
            
        } catch (Exception e) {
            System.err.println("ERROR: Exception occurred:");
            e.printStackTrace(System.err);
            System.out.println("RESULT: ERROR");
        }
    }
}'''
        
        bridge_file = self.bridge_dir / "TweetyQBFBridge.java"
        with open(bridge_file, 'w') as f:
            f.write(java_code)
        
        # Remove old class file to force recompilation
        class_file = self.bridge_dir / "TweetyQBFBridge.class"
        if class_file.exists():
            class_file.unlink()
    
    def _compile_bridge(self):
        try:
            bridge_file = self.bridge_dir / "TweetyQBFBridge.java"
            result = subprocess.run([
                "javac", "-cp", str(self.jar_path), str(bridge_file)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print("COMPILATION ERROR:")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Compilation exception: {e}")
            return False
    
    def evaluate_qbf(self, formula: QBFFormula) -> QBFEvaluationResult:
        import time
        start_time = time.time()
        
        try:
            bridge_class = self.bridge_dir / "TweetyQBFBridge.class"
            if not bridge_class.exists():
                if not self._compile_bridge():
                    return self._error_result(formula, start_time, "Compilation failed")
            
            qbf_content = self._to_qbf_format(formula)
            print(f"DEBUG: QBF content being sent to Java: {qbf_content}");
            
            cmd = [
                "java", "-cp", f"{self.jar_path}:{self.bridge_dir}",
                "TweetyQBFBridge", qbf_content
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            execution_time = time.time() - start_time
            
            # Print debug info
            print(f"DEBUG: Java stdout: {result.stdout}")
            print(f"DEBUG: Java stderr: {result.stderr}")
            print(f"DEBUG: Return code: {result.returncode}")
            
            qbf_result = self._parse_output(result.stdout)
            
            return QBFEvaluationResult(
                formula=formula,
                result=qbf_result,
                execution_time=execution_time,
                solver_output=result.stdout,
                error_message=result.stderr if result.stderr else None
            )
            
        except Exception as e:
            return self._error_result(formula, time.time() - start_time, str(e))
    
    def _to_qbf_format(self, formula: QBFFormula) -> str:
        inner_formula = self._convert_formula_syntax(formula.formula)
        result = inner_formula
        for quant_type, var in reversed(formula.quantifiers):
            result = f"{quant_type} {var}: ({result})"
        return result
    
    def _convert_formula_syntax(self, formula: str) -> str:
        return formula.replace("&", " && ").replace("|", " || ").replace("~", "!")
    
    def _error_result(self, formula: QBFFormula, exec_time: float, error: str) -> QBFEvaluationResult:
        return QBFEvaluationResult(formula, QBFResult.ERROR, exec_time, "", error)
    
    def _parse_output(self, stdout: str) -> QBFResult:
        if "RESULT: SATISFIABLE" in stdout:
            return QBFResult.SATISFIABLE
        elif "RESULT: UNSATISFIABLE" in stdout:
            return QBFResult.UNSATISFIABLE
        else:
            return QBFResult.ERROR

class LLMAssistant:
    def __init__(self, api_key: str, api_endpoint: str = "https://api.openai.com/v1/chat/completions"):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
    
    def text_to_qbf(self, text: str) -> QBFFormula:
        prompt = f"""
        Convert this text to a Quantified Boolean Formula (QBF):
        
        Text: {text}
        
        Provide EXACTLY this format:
        Formula: [use &, |, ~, (, ) with simple variables like p, q, r, s]
        Variables: [comma-separated list]
        Quantifiers: [format: "exists p, forall q"]
        
        Example:
        Formula: s & ~s
        Variables: s
        Quantifiers: forall s
        """
        
        response = self._call_llm(prompt)
        return self._parse_qbf_response(response, text)
    
    def _parse_qbf_response(self, response: str, original_text: str) -> QBFFormula:
        try:
            lines = response.split('\n')
            formula = "p"
            variables = ["p"]
            quantifiers = [("exists", "p")]
            
            for line in lines:
                line = line.strip()
                if line.startswith("Formula:"):
                    formula = line.replace("Formula:", "").strip()
                elif line.startswith("Variables:"):
                    vars_str = line.replace("Variables:", "").strip()
                    if vars_str:
                        variables = [v.strip() for v in vars_str.split(",") if v.strip()]
                elif line.startswith("Quantifiers:"):
                    quant_str = line.replace("Quantifiers:", "").strip()
                    quantifiers = []
                    for q in quant_str.split(","):
                        q = q.strip()
                        if "exists" in q:
                            var = q.replace("exists", "").strip()
                            quantifiers.append(("exists", var))
                        elif "forall" in q:
                            var = q.replace("forall", "").strip()
                            quantifiers.append(("forall", var))
            
            if not variables:
                variables = ["p"]
            if not quantifiers:
                quantifiers = [("forall", variables[0])]
                
            return QBFFormula(formula, variables, quantifiers, original_text)
            
        except Exception:
            return QBFFormula("p", ["p"], [("exists", "p")], original_text)
    
    def _call_llm(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.api_endpoint, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return "Formula: p\nVariables: p\nQuantifiers: exists p"

# Update the main QBF system to use DepQBF
class QBFLogicSystem:
    def __init__(self, jar_path: str, llm_api_key: str, use_depqbf: bool = True):
        if use_depqbf:
            try:
                self.solver = DepQBFSolver()
                logger.info("Using DepQBF solver")
            except RuntimeError as e:
                logger.warning(f"DepQBF not available: {e}, falling back to TweetyProject")
                self.solver = TweetyQBFSolver(jar_path)
        else:
            self.solver = TweetyQBFSolver(jar_path)
        
        self.llm = LLMAssistant(llm_api_key)
    
    def evaluate_text(self, text: str) -> Dict[str, Any]:
        qbf_formula = self.llm.text_to_qbf(text)
        result = self.solver.evaluate_qbf(qbf_formula)
        
        return {
            "original_text": text,
            "qbf_formula": qbf_formula.formula,
            "variables": qbf_formula.variables,
            "quantifiers": qbf_formula.quantifiers,
            "result": result.result.value,
            "execution_time": result.execution_time,
            "solver_output": result.solver_output,
            "error": result.error_message
        }
    
    def evaluate_qbf(self, formula_str: str, variables: List[str], 
                     quantifiers: List[Tuple[str, str]]) -> Dict[str, Any]:
        formula = QBFFormula(formula_str, variables, quantifiers)
        result = self.solver.evaluate_qbf(formula)
        
        return {
            "formula": formula_str,
            "result": result.result.value,
            "execution_time": result.execution_time,
            "solver_output": result.solver_output,
            "error": result.error_message
        }

def main():
    from config import Config
    
    try:
        system = QBFLogicSystem(
            jar_path=str(Config.JAR_PATH),
            llm_api_key=Config.get_api_key()
        )
        
        print("=== QBF Logic System ===")
        
        # Test text conversion
        result = system.evaluate_text("Every student either passes or fails")
        print(f"Text: Every student either passes or fails")
        print(f"QBF: {result['qbf_formula']}")
        print(f"Result: {result['result']}")
        
        # Test direct QBF
        result = system.evaluate_qbf("x | ~x", ["x"], [("forall", "x")])
        print(f"\nDirect QBF: ∀x (x ∨ ¬x)")
        print(f"Result: {result['result']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
