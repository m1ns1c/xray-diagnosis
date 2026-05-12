package com.xray.backend.controller;

import com.xray.backend.config.JwtUtil;
import com.xray.backend.dto.AnalysisResponse;
import com.xray.backend.service.AnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
public class AnalysisController {

    private final AnalysisService analysisService;
    private final JwtUtil jwtUtil;

    @PostMapping("/predict")
    public ResponseEntity<Map<String, Object>> predict(
            @RequestHeader("Authorization") String token,
            @RequestParam("file") MultipartFile file) throws Exception {
        String email = jwtUtil.getEmailFromToken(token.replace("Bearer ", ""));
        Map<String, Object> result = analysisService.analyze(email, file);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/history")
    public ResponseEntity<List<AnalysisResponse>> history(
            @RequestHeader("Authorization") String token) {
        String email = jwtUtil.getEmailFromToken(token.replace("Bearer ", ""));
        List<AnalysisResponse> history = analysisService.getHistory(email)
                .stream()
                .map(AnalysisResponse::new)
                .collect(Collectors.toList());
        return ResponseEntity.ok(history);
    }
}