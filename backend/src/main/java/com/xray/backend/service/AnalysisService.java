package com.xray.backend.service;

import com.xray.backend.entity.Analysis;
import com.xray.backend.entity.User;
import com.xray.backend.repository.AnalysisRepository;
import com.xray.backend.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AnalysisService {

    private final AnalysisRepository analysisRepository;
    private final UserRepository userRepository;
    private final WebClient webClient = WebClient.create("http://localhost:8000");

    public Map<String, Object> analyze(String email, MultipartFile file) throws Exception {
        // Python 서버로 이미지 전송
        ByteArrayResource resource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", resource);

        Map response = webClient.post()
                .uri("/predict")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(Map.class)
                .block();

        // 결과 DB 저장
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("유저를 찾을 수 없습니다."));

        Analysis analysis = new Analysis();
        analysis.setUser(user);
        analysis.setResult((String) response.get("result"));
        analysis.setConfidence(((Number) response.get("confidence")).doubleValue());
        analysis.setImagePath(file.getOriginalFilename());
        analysisRepository.save(analysis);

        return response;
    }

    public List<Analysis> getHistory(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("유저를 찾을 수 없습니다."));
        return analysisRepository.findByUserIdOrderByCreatedAtDesc(user.getId());
    }
}